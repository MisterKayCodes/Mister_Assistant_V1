from aiogram import types
import re
from bot.intents import ActivityIntents, SocialIntents, SystemIntents, TaskIntents
from core.analytics import AnalyticsEngine
from core.parser import Parser
from core.logic import Logic
from data.repository import Repository
from services.media_manager import MediaManager
from utils.formatter import Formatter

class ResponseEngine:
    def __init__(self, db_path):
        self.repo = Repository()
        self.fmt = Formatter()
        self.logic = Logic()
        self.parser = Parser()
        self.analytics = AnalyticsEngine(db_path)
        
        # Inject dependencies into intent modules
        self.activity_intents = ActivityIntents(self.repo, self.fmt, self.logic)
        self.social_intents = SocialIntents(self.repo, self.fmt, self.logic)
        self.system_intents = SystemIntents(self.repo, self.fmt, self.logic, self.analytics)
        self.task_intents = None # Will be initialized via set_scheduler

    async def handle_message(self, message: types.Message):
        user_id = str(message.from_user.id)
        
        # Hydrate cache on every message (or optimize further)
        patterns = self.repo.get_user_patterns(user_id)
        self.parser.cache.load(user_id, patterns)

        text = message.text or message.caption 
        if not text: return

        if text.startswith("/") and text not in ["/start", "/help"]:
            self.repo.clear_pending_media(user_id)
            self.repo.update_user_state(user_id, state_context=None)
            await message.answer(self.fmt.format_info("Action cancelled." if text == "/cancel" else "Command received."))
            return

        state = self.repo.get_user_state(user_id)
        context = state.get("state_context")

        # --- Dispatcher: State Machine ---
        if context == "WAITING_FOR_CAPTION":
            await self.activity_intents.handle_caption(message, user_id, text, self.parser)
        elif context == "WAITING_FOR_CORRECTION_SELECTION":
            await self.activity_intents.handle_correction_selection(message, user_id, text, state)
        elif context == "WAITING_FOR_DELETION_SELECTION":
            await self.activity_intents.handle_deletion_selection(message, user_id, text, state)
        elif context == "WAITING_FOR_LEARNING_INTENT":
            await self._handle_learning_intent(message, user_id, text, state)
        elif context == "WAITING_FOR_GENERALIZATION":
            await self._handle_learning_generalization(message, user_id, text, state)
        elif context == "WAITING_FOR_RESET_CODE":
            await self.system_intents.handle_reset_confirmation(message, user_id, text, state)
        elif context == "WAITING_FOR_TASK_LOG":
            # Senior Refinement #2: Batch Validation
            task = self.repo.get_active_task_group(user_id)
            if task: await self.task_intents.handle_validation(message, user_id, text, task)
            else: self.repo.update_user_state(user_id, state_context=None)
        else:
            await self._handle_intent(message, user_id, text)

    async def handle_intent_directly(self, message, user_id, parsed):
        """Allows handlers to bypass parsing if the intent is already known (e.g. /summary)."""
        await self._dispatch_intent(message, user_id, parsed)

    async def _handle_intent(self, message, user_id, text):
        parsed = self.parser.parse(text, user_id=user_id)
        if not parsed or parsed.get("intent") == "unknown":
            # Senior Refinement: Implicit Context Guard
            # If there's an active task, and the user sends numbers/all, assume validation
            task = self.repo.get_active_task_group(user_id)
            if task and (re.search(r"\d+", text) or text.lower().strip() == "all"):
                if self.task_intents:
                    await self.task_intents.handle_validation(message, user_id, text, task)
                    return

            self.repo.update_user_state(user_id, state_context="WAITING_FOR_LEARNING_INTENT", learning_text=text)
            await message.answer(self.fmt.format_learning_menu(text) + self.fmt.format_footer("WAITING_FOR_LEARNING_INTENT"), parse_mode="Markdown")
            return
        await self._dispatch_intent(message, user_id, parsed)

    async def _handle_learning_intent(self, message, user_id, text, state):
        if text == "/cancel":
            self.repo.update_user_state(user_id, state_context=None, learning_text=None)
            await message.answer("Learning cancelled." + self.fmt.format_footer(), parse_mode="Markdown")
            return
        
        try:
            choice = int(text.strip())
            phrase = state.get("learning_text", "").lower()
            
            # --- OVERRIDE GUARD (CTO Directive) ---
            core_keywords = ["summary", "stop", "done", "starting", "now", "fix", "correct", "actually", "delete", "remove", "/"]
            if any(k in phrase for k in core_keywords):
                self.repo.update_user_state(user_id, state_context=None, learning_text=None)
                await message.answer(self.fmt.format_error("PROHIBITED OVERRIDE: This phrase contains core system 'marrow'. I cannot remap foundational commands.") + self.fmt.format_footer(), parse_mode="Markdown")
                return

            mapping = {1: "start_activity", 2: "stop_activity", 3: "switch_activity", 4: "summary", 5: "log_spending", 6: "ignore"}
            intent = mapping.get(choice)
            if intent == "ignore":
                self.repo.update_user_state(user_id, state_context=None, learning_text=None)
                await message.answer("Ok, ignoring.")
                return
            if intent:
                self.repo.update_user_state(user_id, state_context="WAITING_FOR_GENERALIZATION", last_intent_linked=intent)
                await message.answer(self.fmt.format_generalization_request(state.get("learning_text")), parse_mode="Markdown")
            else:
                await message.answer("Invalid choice.")
        except:
            await message.answer("Please send a number.")

    async def _handle_learning_generalization(self, message, user_id, text, state):
        if text == "/cancel":
            self.repo.update_user_state(user_id, state_context=None, learning_text=None, last_intent_linked=None)
            await message.answer("Learning cancelled." + self.fmt.format_footer(), parse_mode="Markdown")
            return

        phrase = state.get("learning_text")
        intent = state.get("last_intent_linked")
        word = text.strip()
        
        is_template = False
        if word.lower() != "fixed" and word.lower() in phrase.lower():
            # Generalize! Replace word with regex group
            parts = re.split(f"(?i){re.escape(word)}", phrase, 1)
            if len(parts) == 2:
                phrase = f"{re.escape(parts[0])}(?P<name>.+){re.escape(parts[1])}"
                is_template = True
        
        self.repo.add_custom_pattern(user_id, phrase, intent, is_template=is_template)
        self.repo.update_user_state(user_id, state_context=None, learning_text=None, last_intent_linked=None)
        await message.answer(self.fmt.format_success(f"🎓 **Learned!** From now on, `{state.get('learning_text')}` means `{intent}`.") + self.fmt.format_footer(), parse_mode="Markdown")

    async def _dispatch_intent(self, message, user_id, parsed):
        intent = parsed.get("intent")
        response = ""
        # Rule 13: Modular Dispatcher
        modules = [self.activity_intents, self.social_intents, self.system_intents, self.task_intents]
        for module in modules:
            if module is None: continue # Skip if not initialized (e.g. TaskIntents before scheduler)
            method_name = f"intent_{intent}"
            # Mapping legacy names
            if intent == "start_activity": method_name = "intent_start"
            elif intent == "stop_activity": method_name = "intent_stop"
            elif intent == "switch_activity": method_name = "intent_switch"
            elif intent == "delete_activity": method_name = "intent_delete"
            
            if hasattr(module, method_name):
                response = await getattr(module, method_name)(user_id, parsed)
                break
        else:
            response = self.logic.format_unknown()

        if response:
            state = self.repo.get_user_state(user_id)
            await message.answer(response + self.fmt.format_footer(state.get("state_context")), parse_mode="Markdown")

    async def handle_callback(self, callback_query: types.CallbackQuery):
        """Routes callback queries to the appropriate intent module."""
        if self.task_intents:
            await self.task_intents.handle_callback(callback_query)

    def set_scheduler(self, scheduler):
        """Late injection to avoid cyclic imports."""
        self.task_intents = TaskIntents(self.repo, self.fmt, self.logic, scheduler)
