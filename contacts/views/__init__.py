from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import (
    HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404,
    redirect
)
from django.utils import timezone

from contacts.models import (
    Book,
    BookOwner,
)

from gargoyle import gargoyle

class BookOwnerMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if hasattr(request, 'current_book'):
                book = request.current_book
            else:
                try:
                    book = Book.objects.get_for_user(self.request.user)
                except:
                    book = None
            if not book:
                book = Book.objects.create_for_user(self.request.user)
            if gargoyle.is_active('enable_payments', request):
                if book and (not book.paid_until or book.paid_until < timezone.now()):
                    messages.error(request, "Your book is currently unpaid. Please select a subscription, or contact help@contactotter.com")
                    return HttpResponseRedirect('/pricing')
        return super(BookOwnerMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.kwargs.get('book'):
            try:
                bookowner = BookOwner.objects.get(
                    user=self.request.user,
                    book_id=self.kwargs.get('book'),
                )
                return self.model.objects.for_user(
                    self.request.user, book=bookowner.book,
                )
            except BookOwner.DoesNotExist:
                pass
        return self.model.objects.for_user(self.request.user)

    def get_object(self, queryset=None):
        instance = super(BookOwnerMixin, self).get_object(queryset)

        if not instance.can_be_viewed_by(self.request.user):
            raise PermissionDenied

        return instance

    def form_valid(self, form):
        try:
            form.instance.book = BookOwner.objects.get(
                user=self.request.user
            ).book
        except BookOwner.DoesNotExist:
            form.instance.book = Book.objects.create(
                name="{}'s Contacts".format(self.request.user),
            )
            BookOwner.objects.create(book=form.instance.book, user=self.request.user)
        return super(BookOwnerMixin, self).form_valid(form)
