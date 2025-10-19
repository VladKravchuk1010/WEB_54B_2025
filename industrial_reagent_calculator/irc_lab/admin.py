from django.contrib import admin

from irc_lab.models import ChemicalProcess, ReagentCalculation, ChemicalProcessInReagentCalculation

admin.site.register(ChemicalProcess)
admin.site.register(ReagentCalculation)
admin.site.register(ChemicalProcessInReagentCalculation)