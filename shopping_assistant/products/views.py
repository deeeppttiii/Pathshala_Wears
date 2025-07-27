from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm

from .models import Product, Category, ProductReview, ProductImage


@login_required()
def product_list(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    login_form = AuthenticationForm()

    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    # Category filter
    category = request.GET.get('category')
    if category:
        products = products.filter(category__slug=category)

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')

    # Featured products
    featured_products = Product.objects.filter(featured=True)[:4]

    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)

    context = {
        'products': products,
        'categories': categories,
        'current_category': category,
        'current_sort': sort,
        'search_query': query,
        'featured_products': featured_products,
        'login_form': login_form,
    }
    return render(request, 'products/product_list.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'products/category_detail.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    reviews = product.reviews.all().order_by('-created_at')
    images = product.images.all()  # related_name='images' from ProductImage model

    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'images': images,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def add_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # Create or update review
        review, created = ProductReview.objects.get_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )

        if not created:
            review.rating = rating
            review.comment = comment
            review.save()

        return redirect('products:product_detail', slug=product.slug)
    return redirect('products:product_list')
