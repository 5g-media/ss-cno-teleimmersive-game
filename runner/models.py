from django.contrib.postgres.fields import JSONField
from django.db import models

from runner.constants import NO_OP


class Spectator(models.Model):
    """Spectator Model.

    Attributes
    ----------
    group_id : CharField
        Group ID of Spectator
    client_id : CharField
        Client ID of Spectator
    transcoder_no : IntegerField
        The vTranscoder Number
    action_type : CharField
        The type of action to be executed
    action_value : FloatField
        The value related to the action
    profile : IntegerField
        The currently consumed vTranscoder profile
    has_received_metrics : BooleanField
        Have initial metrics been received?
    measurements : JSONField
        Lately collected measurements in JSON form
    mos_score : FloatField
        Lately collected MOS

    """
    group_id = models.CharField(max_length=255, help_text='Group ID of Spectator', null=False)
    client_id = models.CharField(max_length=255, help_text='Client ID of Spectator', null=False)
    transcoder_no = models.IntegerField(default=0, help_text='Transcoder number', null=False)
    action_type = models.CharField(max_length=255, default=NO_OP, help_text='The type of action to NS', null=False)
    action_value = models.FloatField(default=-1, help_text='The value related to action type', null=False)
    profile = models.IntegerField(default=0, help_text='The value related to the state', null=False)
    has_received_metrics = models.BooleanField(default=False, help_text='Are initial metrics received', null=False)
    measurements = JSONField(help_text='Last collected measurements in JSON form', null=True)
    mos_score = models.FloatField(default=3.0, help_text='Last collected MOS score', null=True)


class VTranscoder(models.Model):
    """VTranscoder Model Class.

    Attributes
    ----------
    vnf_id : CharField
        The VNF ID of the vTranscoder
    processing_unit : CharField
        The type of processing unit that the vTranscoder is running on
    produced_qualities : JSONField
        The list of qualities produced by the vTranscoder
    mano_payload : JSONField
        The MANO payload to send along with the proper action

    """
    vnf_id = models.CharField(max_length=100, help_text='The VNF id of the vTranscoder')
    processing_unit = models.CharField(max_length=8, help_text='The vTranscoder\'s processing unit')
    produced_qualities = JSONField(help_text='The profiles that are currently produced by the vTranscoder')
    mano_payload = JSONField(help_text='The MANO payload to send along with the action upon a decision', null=True)
