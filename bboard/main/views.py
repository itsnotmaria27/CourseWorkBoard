from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.views import LoginView, LogoutView, \
     PasswordChangeView, PasswordResetView, PasswordResetDoneView, \
     PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import UpdateView, CreateView, \
                                      DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.core.signing import BadSignature
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import AdvUser,  SubRubric, Bb, Comment
from .forms import ProfileEditForm, RegisterForm, SearchForm, \
     BbForm, AIFormSet, UserCommentForm, GuestCommentForm, RatingForm
from .utilities import signer
from django.shortcuts import render

def test_403(request):
    return render(request, '403.html', status=403)


def index(request):
    bbs = Bb.objects.filter(is_active=True).select_related('rubric')[:10]
    context = {'bbs': bbs}
    return render(request, 'main/index.html', context)

def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))

class BBLoginView(LoginView):
    template_name = 'main/login.html'

@login_required
def profile(request):
    bbs = Bb.objects.filter(author=request.user.pk)
    context = {'bbs': bbs}
    return render(request, 'main/profile.html', context)

class BBLogoutView(LogoutView):
    pass

class ProfileEditView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

class PasswordEditView(SuccessMessageMixin, LoginRequiredMixin,
                                            PasswordChangeView):
    template_name = 'main/password_edit.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменен'

class RegisterView(CreateView):
    model = AdvUser
    template_name = 'main/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('main:register_done')

class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'

def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/activation_failed.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'main/activation_done_later.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)

class ProfileDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/profile_delete.html'
    success_url = reverse_lazy('main:index')
    success_message = 'Пользователь удален'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class BBPasswordResetView(PasswordResetView):
    template_name = 'main/password_reset.html'
    subject_template_name = 'email/reset_letter_subject.txt'
    email_template_name = 'email/reset_letter_body.txt'
    success_url = reverse_lazy('main:password_reset_done')

class BBPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'main/password_reset_done.html'

class BBPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'main/password_reset_confirm.html'
    success_url = reverse_lazy('main:password_reset_complete')

class BBPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'main/password_reset_complete.html'

def test_500(request):
    raise Exception("Тестовая ошибка 500")

def rubric_bbs(request, pk):
    rubric = get_object_or_404(SubRubric, pk=pk)
    bbs = Bb.objects.filter(is_active=True, rubric=pk)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        q = Q(title__icontains=keyword) | Q(content__icontains=keyword)
        bbs = bbs.filter(q)
    else:
        keyword = ''
    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 2)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'rubric': rubric, 'page': page, 'bbs': page.object_list,
               'form': form}
    return render(request, 'main/rubric_bbs.html', context)

def bb_detail(request, rubric_pk, pk):
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=pk, is_active=True)

    # --- Обработка комментариев ---
    initial = {'bb': bb.pk}
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        comment_form_class = UserCommentForm
    else:
        comment_form_class = GuestCommentForm

    comment_form = comment_form_class(initial=initial)

    if request.method == 'POST' and 'comment_submit' in request.POST:
        c_form = comment_form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.success(request, 'Комментарий добавлен')
            return redirect(request.get_full_path_info())
        else:
            comment_form = c_form
            messages.warning(request, 'Комментарий не добавлен')

    # --- Обработка рейтинга ---
    rating_form = None
    if request.user.is_authenticated:
        rating_form = RatingForm()

        if request.method == 'POST' and 'rating_submit' in request.POST:
            r_form = RatingForm(request.POST)
            if r_form.is_valid():
                rating, created = bb.rating_set.update_or_create(
                    user=request.user,
                    defaults={'score': r_form.cleaned_data['score']}
                )
                messages.success(request, 'Ваша оценка сохранена!' if created else 'Ваша оценка обновлена.')
                return redirect(request.get_full_path_info())
            else:
                rating_form = r_form
                messages.warning(request, 'Ошибка при сохранении оценки.')

    # --- Контекст ---
    context = {
        'bb': bb,
        'ais': ais,
        'comments': comments,
        'form': comment_form,          # форма комментария (для шаблона)
        'rating_form': rating_form,    # форма рейтинга (может быть None)
    }
    return render(request, 'main/bb_detail.html', context)

@login_required
def profile_bb_detail(request, pk):
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=pk, is_active=True)
    context = {'bb': bb, 'ais': ais, 'comments': comments}
    return render(request, 'main/profile_bb_detail.html', context)


@login_required
def profile_bb_add(request):
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Объявление добавлено')
                return redirect('main:profile')
    else:
        form = BbForm(initial={'author': request.user.pk})
        formset = AIFormSet()
    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_bb_add.html', context)

@login_required
def profile_bb_edit(request, pk):
    bb = get_object_or_404(Bb, pk=pk)
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES, instance=bb)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Объявление исправлено')
                return redirect('main:profile')
    else:
        form = BbForm(instance=bb)
        formset = AIFormSet(instance=bb)
    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_bb_edit.html', context)



@login_required
def profile_bb_delete(request, pk):
    bb = get_object_or_404(Bb, pk=pk)
    if request.method == 'POST':
        bb.delete()
        messages.add_message(request, messages.SUCCESS, 'Объявление удалено')
        return redirect('main:profile')
    else:
        context = {'bb': bb}
        return render(request, 'main/profile_bb_delete.html', context)
    
@login_required
def add_rating(request, rubric_pk, pk):
    bb = get_object_or_404(Bb, pk=pk)
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating, created = bb.ratings.update_or_create(
                user=request.user,
                defaults={'score': form.cleaned_data['score']}
            )
            if created:
                messages.success(request, 'Ваша оценка сохранена!')
            else:
                messages.info(request, 'Ваша оценка обновлена.')
        else:
            messages.error(request, 'Ошибка при сохранении оценки.')
    return redirect('main:bb_detail', rubric_pk=rubric_pk, pk=pk)
