from database.enum import OrderStatusType as Status

TRANSITIONS = {
    Status.NEW: (Status.ASSIGNED, Status.IN_PROGRESS, Status.CANCELED),
    Status.ASSIGNED: (Status.IN_PROGRESS, Status.CANCELED),
    Status.IN_PROGRESS: (Status.COMPLETED, Status.CANCELED),
    Status.COMPLETED: (),
    Status.CANCELED: (),
}
ACTIVE_STATUSES = (Status.NEW, Status.ASSIGNED, Status.IN_PROGRESS)
