from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from .models import Product, Store
from .forms import ProductForm, StoreForm
from django.http import Http404, HttpResponse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

# Funkcja do sprawdzania istnienia szablonu HTML
def check_template(template_name, request):
    try:
        get_template(template_name)
    except TemplateDoesNotExist:
        messages.error(request, 'Brak pliku HTML')
        return False
    return True

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not check_template(self.template_name, self.request):
            return HttpResponse("Brak pliku .html")

        remember_me = form.cleaned_data.get('remember_me', False)
        if remember_me:
            self.request.session.set_expiry(1209600)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('store-list')

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'signup.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")

        if request.user.is_authenticated:
            return redirect('logout')

        return super().dispatch(request, *args, **kwargs)

class CustomLogoutView(LoginRequiredMixin, LogoutView):
    next_page = 'login'

class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserChangeForm
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('notifications')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")

        if not request.user.is_authenticated:
            messages.error(request, 'Nie jesteś zalogowany.')
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    template_name = 'delete_account.html'
    success_url = reverse_lazy('login_existing')

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return redirect('post_detail')

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        user = self.request.user
        if user.is_authenticated:
            return user
        else:
            raise Http404("Nie jesteś zalogowany.")

    def delete(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Wystąpił błąd: {str(e)}")
            return redirect('delete_account')

class AddProductView(LoginRequiredMixin, CreateView):
    form_class = ProductForm
    template_name = 'add_product.html'

    def form_valid(self, form):
        store_id = self.kwargs.get('store_pk')
        store = get_object_or_404(Store, pk=store_id, user=self.request.user)
        form.instance.owner = store
        response = super().form_valid(form)

        # Nie ustawiamy success_url tutaj

        return response

    def get_success_url(self):
        # Zwracamy odpowiednią ścieżkę z identyfikatorem nowo utworzonego produktu
        store_id = self.kwargs.get('store_pk')
        product_id = self.object.pk
        return reverse('lower-prices', kwargs={'store_pk': store_id, 'product_pk': product_id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class StoreListView(ListView):
    model = Store
    template_name = 'store_list.html'  # Twój szablon HTML dla listy sklepów
    context_object_name = 'stores'  # Nazwa zmiennej kontekstu, która będzie zawierać listę sklepów

    def get_queryset(self):
        return Store.objects.all()  # Pobierz wszystkie sklepy
    
class UpdateProductView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'update_product.html'

    def get_object(self, queryset=None):
        store_pk = self.kwargs.get('store_pk')
        product_pk = self.kwargs.get('product_pk')
        return get_object_or_404(Product, pk=product_pk, owner__pk=store_pk)

    def form_valid(self, form):
        store = self.get_object().owner
        if store.user == self.request.user:
            return super().form_valid(form)
        else:
            return HttpResponse("Nie jesteś upoważniony do konfiguracji produktu")

    def get_success_url(self):
        store_id = self.kwargs.get('store_pk')
        product_id = self.object.pk
        return reverse('product-update', kwargs={'store_pk': store_id, 'product_pk': product_id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)

class DeleteProductView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'delete_product.html'

    def get_object(self, queryset=None):
        store_pk = self.kwargs.get('store_pk')
        product_pk = self.kwargs.get('product_pk')
        return get_object_or_404(Product, pk=product_pk, owner__pk=store_pk)

    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        if product.owner.user == self.request.user:
            return super().delete(request, *args, **kwargs)
        else:
            return HttpResponse("You are not authorized to delete this product.")

    def get_success_url(self):
        store_id = self.get_object().owner.pk
        return reverse('product-list', kwargs={'store_pk': store_id})

    def dispatch(self, request, *args, **kwargs):
        if not check_template(self.template_name, request):
            return HttpResponse("Template file not found.")
        return super().dispatch(request, *args, **kwargs)

class AddStoreView(LoginRequiredMixin, CreateView):
    form_class = StoreForm
    template_name = 'add_store.html'
    success_url = reverse_lazy('store-list')  # Poprawiono przekierowanie po sukcesie

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        # Sprawdź czy szablon jest poprawnie załadowany
        if not check_template(self.template_name, request):
            return HttpResponse("Brak pliku .html")
        return super().dispatch(request, *args, **kwargs)
    
class StoreDetailView(DetailView):
    model = Store
    template_name = 'store_detail.html'
    context_object_name = 'store'
    
@transaction.atomic
def display_records_with_lower_prices(request, store_pk, product_pk):
    if request.user.is_authenticated:
        template_name = 'templates_with_records.html'
        if not check_template(template_name, request):
            return HttpResponse("Brak pliku .html")

        try:
            product = get_object_or_404(Product, pk=product_pk, owner__pk=store_pk)
            products_with_lower_prices = Product.objects.filter(name=product.name, price__lt=product.price, owner__pk=store_pk)
            return render(request, 'templates_with_records.html', {'components': products_with_lower_prices})
        except Product.DoesNotExist:
            messages.error(request, 'Produkt o podanym identyfikatorze nie istnieje.')
            return redirect('login')
    else:
        messages.error(request, 'Nie jesteś zalogowany.')
        return redirect('login')
    
@transaction.atomic
def read_products_for_category(request):
    template_name = 'comment.html'
    if not check_template(template_name, request):
        return HttpResponse("Brak pliku .html")

    category = request.GET.get('category')

    if category:  # Jeżeli wybrano kategorię
        products = Product.objects.filter(category__name=category)  # Poprawiono filtrowanie po nazwie kategorii
    else:  # Jeżeli nie wybrano kategorii
        products = Product.objects.all()

    return render(request, template_name, {'products': products, 'caregory': category})

@transaction.atomic
def search_products(request):
    template_name = 'search_results.html'
    if not check_template(template_name, request):
        return HttpResponse("Brak pliku .html")

    query = request.GET.get('q')

    if query:  # Jeżeli wprowadzono zapytanie w wyszukiwarce
        # Szukamy produktów, których nazwa zawiera wprowadzone zapytanie
        products = Product.objects.filter(name__icontains=query)
    else:  # Jeżeli nie wprowadzono zapytania
        products = Product.objects.all()

    return render(request, template_name, {'products': products, 'query': query})