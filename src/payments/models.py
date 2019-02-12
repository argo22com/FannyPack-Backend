import uuid
from datetime import datetime
from operator import itemgetter

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractUser
from django.db import models, transaction

# from payments.utils.optimization import Optimization
from fannypack import settings


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    secret = models.CharField(max_length=512, blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def create_room(user: 'User', name, secret=None):
        room = Room(
            name=name,
        )

        if secret is not None:
            room.secret = make_password(secret)

        room.save()

        room.user_set.add(user)

        return room

    def get_user_balances(self):
        all_payments = self.payment_set.prefetch_related('pledger', 'split_set', 'split_set__user').all()
        users = self.user_set.all()
        debts = {}
        payments = {}

        for payment in all_payments:
            payments[payment.pledger_id] = payments.get(payment.pledger_id, 0) + payment.get_amount()
            for split in payment.split_set.all():
                debts[split.user_id] = debts.get(split.user_id, 0) + split.amount

        balances = []
        for user in users:
            balances.append({
                'user': user,
                'debts': debts.get(user.id, 0),
                'payments': payments.get(user.id, 0),
                'balance': debts.get(user.id, 0) - payments.get(user.id, 0),
            })

        balances_sorted = sorted(balances, key=itemgetter('balance'), reverse=True)

        return balances_sorted

    def get_resolution(self):
        balances = self.get_user_balances()
        if len(balances) < 2:
            return []

        if self._is_resolved(balances):
            return []
        steps = []
        while not self._is_resolved(balances):
            balances, step = self._get_next_resolution_step(balances)
            steps.append(step)

        return steps

    def _is_resolved(self, balances):
        bs = sorted(balances, key=itemgetter('balance'), reverse=True)
        return bs[0]['balance'] == bs[-1]['balance']

    def _get_next_resolution_step(self, balances):
        bs = sorted(balances, key=itemgetter('balance'), reverse=True)
        payer = bs[0]
        recipient = bs[-1]
        if payer['balance'] >= abs(recipient['balance']):
            amount = abs(recipient['balance'])
        else:
            amount = abs(payer['balance'])

        payer['balance'] = payer['balance'] - amount
        recipient['balance'] = recipient['balance'] + amount
        return (
            bs,
            {
                'payer': payer['user'],
                'recipient': recipient['user'],
                'amount': amount
            }
        )


class User(AbstractUser):
    rooms = models.ManyToManyField(Room)

    def join_room(self, room: 'Room', secret: str = None):
        if room.secret and not check_password(secret, room.secret):
            raise Exception('Invalid room secret')

        self.rooms.add(room)
        self.save()
        return self


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pledger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Pledger")
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    date = models.DateTimeField()
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name if self.name else 'unnamed payment'

    @staticmethod
    @transaction.atomic
    def create_payment(room: Room, pledger: User, name: str, splits, date: datetime):
        payment = Payment.objects.create(
            pledger=pledger,
            room=room,
            name=name,
            date=date,
        )

        for split in splits:
            payment.add_split(split['user'], split['amount'])

        payment.refresh_from_db()
        return payment

    def add_split(self, user, amount):
        return Split.objects.create(
            payment=self,
            user=user,
            amount=amount
        )

    def get_amount(self):
        splits = self.split_set.all()
        amount = 0
        for split in splits:
            amount += split.amount

        return amount

    def delete(self, using=None, keep_parents=False):
        return super().delete(using, keep_parents)


class Split(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="Drawee")
    amount = models.FloatField()
