class SocialIntents:
    def __init__(self, repo, fmt, logic):
        self.repo = repo
        self.fmt = fmt
        self.logic = logic

    async def intent_add_person(self, uid, p):
        self.repo.add_person(uid, p.get("name"), p.get("relationship"))
        return self.fmt.format_success(self.logic.format_person_added(p.get("name"), p.get("relationship")))

    async def intent_log_spending(self, uid, p):
        self.repo.log_spending(uid, p.get("amount"), p.get("category"))
        return self.fmt.format_success(self.logic.format_spending_logged(p.get("amount"), p.get("category")))

    async def intent_check_activity(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        if aid:
            name = self.repo.get_activity_name(aid)
            return self.fmt.format_info(self.logic.format_check_message(name))
        return self.fmt.format_error("Not tracking.")
