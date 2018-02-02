from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

from opensubmit import admin, api
from opensubmit.views import frontend, backend, lti
from opensubmit.forms import MailForm

urlpatterns = [
    url(r'^$', frontend.IndexView.as_view(), name='index'),
    url(r'^logout/$', frontend.LogoutView.as_view(), name='logout'),
    url(r'^settings/$', frontend.SettingsView.as_view(), name='settings'),
    url(r'^courses/$', frontend.CoursesView.as_view(), name='courses'),
    url(r'^archive/$', frontend.ArchiveView.as_view(), name='archive'),
    url(r'^dashboard/$', frontend.DashboardView.as_view(), name='dashboard'),
    url(r'^details/(?P<pk>\d+)/$', frontend.SubmissionDetailsView.as_view(), name='details'),
    url(r'^machine/(?P<pk>\d+)/$', frontend.MachineDetailsView.as_view(), name='machine'),
    url(r'^assignments/(?P<pk>\d+)/new/$', frontend.SubmissionNewView.as_view(), name='new'),
    url(r'^withdraw/(?P<pk>\d+)/$', frontend.SubmissionWithdrawView.as_view(), name='withdraw'),
    url(r'^update/(?P<pk>\d+)/$', frontend.SubmissionUpdateView.as_view(), name='update'),

    url(r'^teacher/', include(admin.teacher_backend.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^preview/(?P<pk>\d+)/$', backend.PreviewView.as_view(), name='preview'),
    url(r'^assignments/(?P<pk>\d+)/duplicates/$', backend.DuplicatesView.as_view(), name='duplicates'),
    url(r'^assignments/(?P<pk>\d+)/archive/$', backend.AssignmentArchiveView.as_view(), name='assarchive'),
    url(r'^course/(?P<pk>\d+)/archive/$', backend.CourseArchiveView.as_view(), name='coursearchive'),
    url(r'^course/(?P<pk>\d+)/gradingtable/$', backend.GradingTableView.as_view(), name='gradingtable'),
    url(r'^mergeusers/(?P<primary_pk>\d+)/(?P<secondary_pk>\d+)/$', backend.MergeUsersView.as_view(), name='mergeusers'),
    url(r'^mail/receivers=(?P<user_list>.*)$', backend.MailFormPreview(MailForm), name='mailstudents'),
    url(r'^mail/course=(?P<course_id>\d+)$', backend.MailFormPreview(MailForm), name='mailcourse'),

    url(r'^jobs/$', api.jobs, name='jobs'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/secret=(?P<secret>\w+)$', api.download, name='download_secret'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/$', api.download, name='download'),
    url(r'^machines/$', api.machines, name='machines'),

    url(r'^lti/$', lti.login, name='lti'),
    url(r'^lti/config/$', lti.config, name='lticonfig'),

    url('', include('social_django.urls', namespace='social')),

    url(r'^403/$', TemplateView.as_view(template_name='403.html')),
    url(r'^404/$', TemplateView.as_view(template_name='404.html')),
    url(r'^500/$', TemplateView.as_view(template_name='500.html')),
]

# only working when DEBUG==FALSE
# on production systems, static files are served directly by Apache
urlpatterns += staticfiles_urlpatterns()


def show_urls(urllist, depth=0):  # pragma: no cover
    for entry in urllist:
        print("  " * depth, entry.regex.pattern)
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)
# show_urls(urlpatterns)
