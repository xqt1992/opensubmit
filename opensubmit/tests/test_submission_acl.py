from opensubmit.tests.cases import *

from opensubmit.models import Course, Assignment, Submission
from opensubmit.models import Grading, GradingScheme
from opensubmit.models import UserProfile


class StudentACLTestCase(SubmitTestCase):
    def setUp(self):
        super(StudentACLTestCase, self).setUp()
        self.loginUser(self.enrolled_students[0])

    def createSubmissions(self):
        self.openAssignmentSub = self.createSubmission(self.current_user, self.openAssignment)
        self.softDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.softDeadlinePassedAssignment)
        self.hardDeadlinePassedAssignmentSub = self.createSubmission(self.current_user, self.hardDeadlinePassedAssignment)
        
        self.submissions = (
            self.openAssignmentSub,
            self.softDeadlinePassedAssignmentSub,
            self.hardDeadlinePassedAssignmentSub,
        )

    def testCanCreateSubmission(self):
        self.assertEquals(self.openAssignment.can_create_submission(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), True)

    def testCannotCreateSubmissionAfterDeadline(self):
        self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)

    def testCannotCreateSubmissionBeforePublishing(self):
        self.assertEquals(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)

    def testAdminTeacherTutorAlwaysCanCreateSubmission(self):
        for user in (self.admin, self.teacher, self.tutor, ):
            self.assertEquals(self.openAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(user.user), True)
            self.assertEquals(self.unpublishedAssignment.can_create_submission(user.user), True)

    def testCannotDoubleSubmit(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.softDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.hardDeadlinePassedAssignment.can_create_submission(self.current_user.user), False)
        self.assertEquals(self.unpublishedAssignment.can_create_submission(self.current_user.user), False)

    def testCanWithdrawSubmission(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignmentSub.can_withdraw(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), True)

    def testCannotWithdrawSubmissionAfterDeadline(self):
        self.createSubmissions()
        self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_withdraw(self.current_user.user), False)

    def testCanModifySubmission(self):
        self.createSubmissions()
        self.assertEquals(self.openAssignmentSub.can_modify(self.current_user.user), True)
        self.assertEquals(self.softDeadlinePassedAssignmentSub.can_modify(self.current_user.user), True)

    def testCannotModifySubmissionAfterDeadline(self):
        self.createSubmissions()
        self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_modify(self.current_user.user), False)

    def testCanOrCannotReuploadSubmissions(self):
        self.createSubmissions()
        for state, desc in Submission.STATES:
            for submission in self.submissions:
                submission.state = state
                submission.save()

            # Submissions should only be allowed to be re-uploaded if:
            # 1. The code has already been uploaded and executed and
            # 2. the execution has failed, and
            # 3. the hard deadline has not passed.
            if state in (
                Submission.TEST_COMPILE_FAILED,
                Submission.TEST_VALIDITY_FAILED,
                Submission.TEST_FULL_FAILED,
            ):
                self.assertEquals(self.openAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEquals(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), True)
                self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
            else:
                self.assertEquals(self.openAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEquals(self.softDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)
                self.assertEquals(self.hardDeadlinePassedAssignmentSub.can_reupload(self.current_user.user), False)

    def testCannotUseTeacherBackend(self):
        response = self.c.get('/teacher/opensubmit/submission/')
        self.assertEquals(response.status_code, 302)        # Redirect to login page

    def testCannotUseAdminBackend(self):
        response = self.c.get('/admin/auth/user/')
        self.assertEquals(response.status_code, 302)        # Redirect to login page

