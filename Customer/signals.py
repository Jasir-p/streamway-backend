from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Accounts,Contact


@receiver(post_save, sender=Accounts)
def update_primary_contact(sender, instance, **kwargs):
    primary_contact = instance.contacts.filter(is_primary_contact=True).first()
    if not primary_contact:
        primary_contact = instance.contacts.first()
    update_fields = []

    if primary_contact.name != instance.name:
        primary_contact.name = instance.name
        update_fields.append('name')
    
    if primary_contact.email != instance.email:
        primary_contact.email = instance.email
        update_fields.append('email')
    
    if primary_contact.phone_number != instance.phone_number:
        primary_contact.phone_number = instance.phone_number
        update_fields.append('phone_number')


    if update_fields:
        primary_contact.save(update_fields=update_fields)