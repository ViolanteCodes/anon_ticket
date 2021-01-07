from django import forms
from django.forms import ModelForm
from django.conf import settings
from django.shortcuts import get_object_or_404
import gitlab
import random
from .models import Project, Issue, UserIdentifier

# Initialize GitLab Object
gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=settings.GITLAB_SECRET_TOKEN)

class LoginForm(forms.Form):
    """A form that allows users to enter in their keycodes to login."""
    word_1 = forms.CharField(max_length=9)
    word_2 = forms.CharField(max_length=9)
    word_3 = forms.CharField(max_length=9)
    word_4 = forms.CharField(max_length=9)
    word_5 = forms.CharField(max_length=9)
    word_6 = forms.CharField(max_length=9)

    def join_words(self):
        """Pull cleaned data from form and join into code_phrase"""
        word_list = []
        word_list.append(self.cleaned_data['word_1'])
        word_list.append(self.cleaned_data['word_2'])
        word_list.append(self.cleaned_data['word_3'])
        word_list.append(self.cleaned_data['word_4'])
        word_list.append(self.cleaned_data['word_5'])
        word_list.append(self.cleaned_data['word_6'])
        join_key = '-'
        code_phrase = join_key.join(word_list)
        return code_phrase

class Anonymous_Ticket_Base_Search_Form(forms.Form):
    """A base search form with all the methods necessary to search for
    projects, issues, and tickets."""

    def project_search(self):
        """Pass the data from the project_id to github and look up the 
        project details."""
        # Setup a results dictionary
        result = {}
        # Setup messages dictionary for project.
        messages = {
            'gitlab_project_not_found_message': """This project could not be 
            fetched from gitlab. It likely does not exist, or you don't 
            have access to it.""",
            'unknown_project_error_message': """This lookup failed for 
            a reason not currently accounted for by our current error 
            handling.""",
        }
        result['project_status'] = 'pending'
        if self.cleaned_data['choose_project']:
            working_project_name = self.cleaned_data['choose_project']
        # Try to grab project matching form selection out of database.
        try: 
            working_project = get_object_or_404(
                Project, project_name=working_project_name)
        # Once Project is found, grab project info from gitlab.
            try:
                id_to_grab = working_project.project_id 
                linked_project = gl.projects.get(id_to_grab)
            # if project does not exist (python-gitlab raises GitlabGetError)
            # pass failed status and failure message into result dictionary.
            except gitlab.exceptions.GitlabGetError:
                result['project_status'] = 'failed'
                result['project_message'] = messages['gitlab_project_not_found_message']
            except:
                result['project_message'] = messages['unknown_project_error_message']
                result['project_status'] = 'failed'
        except Project.DoesNotExist:
            raise Http404("No Project matches the given query.")
        except:
            pass
        # If successful on project lookup, add project as attribute to
        # form Object and save project in dictionary as 'matching_project'.
        if result['project_status'] != 'failed':    
            self.linked_project = linked_project
            result['status'] = 'pending'
            result['matching_project'] = linked_project
        return result

    def issue_search(self, project_result={}):
        """Pass the data from the search_term CharField to github and 
        look up the project details."""
        result = project_result
        messages = {
            'could_not_fetch_issue_message': """Your project was found, but 
            this issue could not be fetched from gitlab. It likely does 
            not exist, or you don't have access to it.""",
            'successful_issue_lookup_message': """Issues were found matching this search string.""",
            'no_matching_issues_message': """Your search executed successfully,
            but no issues matching this search string were found.""",
            'unknown_issue_error_message': """This lookup failed for
            unknown reasons."""
        }
        if result['status'] == 'pending':
            search_string = self.cleaned_data['search_terms']
            result['search_string'] = search_string
            try:
                search_issues = self.linked_project.search('issues', search_string)
                result['matching_issues'] = search_issues
                if result['matching_issues']:
                    result['status'] = 'success'
                    result['message'] = messages['successful_issue_lookup_message']
                else:
                    result['status'] = 'no matches'
                    result['message'] = messages['no_matching_issues_message']
            except gitlab.exceptions.GitlabGetError:
                result['status'] = 'failed'
                result['message'] = messages['could_not_fetch_issue_message']
            except:
                result['status'] = 'failed'
                result['message'] = messages['unknown_issue_error_message']                
        return result

    def call_project_and_issue(self):
        """Call the project_search and issue_search methods and send the
        relevant information to GitLab to look up a ticket."""
        project_result = self.project_search()
        result = self.issue_search(project_result=project_result)
        return result

class Anonymous_Ticket_Project_Search_Form(Anonymous_Ticket_Base_Search_Form):
    """A form to let users search for an issue or notes matching a project string."""
    
    choose_project = forms.ModelChoiceField(
        queryset=Project.objects.all(), 
        label="Choose a project.",
        help_text="Not all Tor projects can be searched via this portal."
        )
    search_terms = forms.CharField(
        max_length=200,
        label="Enter a short search string.",
        help_text="""Shorter strings are better, as this search will find
        exact matches only."""
        )

class CreateIssueForm(ModelForm):
    class Meta:
        model = Issue
        fields = ('linked_project', 'issue_title', 'issue_description')
        labels = {
            'linked_project': ('Linked Project'),
            'issue_title': ('Title of Your Issue'),
            'issue_description': ('Describe Your Issue'),
        }
        help_texts = {
            'linked_project': ("""Choose the project associated with this issue."""),
            'issue_title': ("""Give your issue a descriptive title."""),
            'issue_description': ("""Describe the issue you are reporting. 
            Please be as specific as possible about the circumstances that
            provoked the issue and the behavior that was noticed."""),
        }






