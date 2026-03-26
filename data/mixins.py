from data.mixins.base import BaseMixin, StateMixin, SpendingMixin, PeopleMixin, ReminderMixin
from data.mixins.activity import ActivityMixin
from data.mixins.media import MediaMixin
from data.mixins.learning import LearningMixin
from data.mixins.task_mixin import TaskMixin

# This file is now a proxy to satisfy the 200-line requirement while maintaining the legacy API.
__all__ = [
    'BaseMixin', 'StateMixin', 'SpendingMixin',
    'PeopleMixin', 'ReminderMixin', 'ActivityMixin', 'MediaMixin', 'LearningMixin', 'TaskMixin'
]
