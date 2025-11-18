from django.urls import path, include
from .api_views import (
    ChemicalProcessList,
    ChemicalProcessDetail,
    chemical_process_upload_image,
    CartIconView,
    ReagentCalculationList,
    ReagentCalculationDetail,
    calculation_form,
    calculation_complete,
    add_process_to_cart,
    update_calculation_process,
    delete_calculation_process,
    user_register,
    user_profile,
    user_logout,
    user_login
)

app_name = 'irc_lab_api'

urlpatterns = [
    # ChemicalProcess endpoints
    path('chemical-processes/', ChemicalProcessList.as_view(), name='chemical-process-list'),
    path('chemical-processes/<int:pk>/', ChemicalProcessDetail.as_view(), name='chemical-process-detail'),
    path('chemical-processes/<int:pk>/image/', chemical_process_upload_image, name='chemical-process-image'),
    path('chemical-processes/<int:pk>/add-to-cart/', add_process_to_cart, name='add-to-cart'),

    # ReagentCalculation endpoints
    path('reagent_calculations/cart-icon/', CartIconView.as_view(), name='cart-icon'),
    path('reagent_calculations/', ReagentCalculationList.as_view(), name='calculation-list'),
    path('reagent_calculations/<int:pk>/', ReagentCalculationDetail.as_view(), name='calculation-detail'),
    path('reagent_calculations/<int:pk>/form/', calculation_form, name='calculation-form'),
    path('reagent_calculations/<int:pk>/complete/', calculation_complete, name='calculation-complete'),

    # ChemicalProcessInReagentCalculation endpoints
    path('calculation-processes/', update_calculation_process, name='calculation-process-update'),
    path('calculation-processes/delete/', delete_calculation_process, name='calculation-process-delete'),

    # User endpoints
    path('user/register/', user_register, name='user-register'),
    path('user/profile/', user_profile, name='user-profile'),
    path('user/login/', user_login, name='user-login'),
    path('user/logout/', user_logout, name='user-logout'),
]