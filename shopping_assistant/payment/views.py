from django.shortcuts import render, redirect
from django.http import HttpResponse

def esewa_payment(request):
    # Simulated eSewa payment success
    return HttpResponse("eSewa Payment Processed Successfully!")

def khalti_payment(request):
    # Simulated Khalti payment success
    return HttpResponse("Khalti Payment Processed Successfully!")
