from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from .models import Job, Application
from .forms import JobForm, ApplicationForm, SignUpForm
from django.db.models import Q


# Role checker helper
def is_employer(user):
    return user.groups.filter(name='Employer').exists()

def is_applicant(user):
    return user.groups.filter(name='Applicant').exists()

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            group = 'Employer' if role == 'employer' else 'Applicant'
            user.groups.add(Group.objects.get_or_create(name=group)[0])
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'jobs/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'jobs/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    if is_employer(request.user):
        jobs = Job.objects.filter(posted_by=request.user)
        return render(request, 'jobs/employer_dashboard.html', {'jobs': jobs})
    elif is_applicant(request.user):
        applications = Application.objects.filter(applicant=request.user)
        return render(request, 'jobs/applicant_dashboard.html', {'applications': applications})
    return redirect('login')

@login_required
def post_job(request):
    if not is_employer(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            return redirect('dashboard')
    else:
        form = JobForm()
    return render(request, 'jobs/post_job.html', {'form': form})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'jobs/job_detail.html', {'job': job})

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            return redirect('dashboard')
    else:
        form = ApplicationForm()
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})


def job_list(request):
    query = request.GET.get('q')
    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        )

    return render(request, 'jobs/job_list.html', {'jobs': jobs, 'query': query})


