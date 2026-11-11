from django.db import models

class CurrencyType(models.TextChoices):
    USD = "USD", "USD"
    BDT = "BDT", "BDT"

class StatusType(models.TextChoices):
    INITIATED = "INITIATED", "INITIATED"
    PROCESSING = "PROCESSING", "PROCESSING"
    SUSPENDED = "SUSPENDED", "SUSPENDED"
    REVERSED = "REVERSED", "REVERSED"
    COMPLETED = "COMPLETED", "COMPLETED"

class   TransactionType(models.TextChoices):
    ADD_MONEY = "ADD_MONEY", "ADD_MONEY"
    TRANSFER_IN = "TRANSFER_IN", "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT", "TRANSFER_OUT"
    WITHDRAWAL = "WITHDRAWAL", "WITHDRAWAL"

class OperationType(models.TextChoices):
    ADD_MONEY = "ADD_MONEY", "ADD_MONEY"
    P2P_TRANSFER = "P2P_TRANSFER", "P2P_TRANSFER"

class WithdrawalMethod(models.TextChoices):
    BANK = "BANK", "Bank"
    AGENT = "AGENT", "Agent"