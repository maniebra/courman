"""The action catalogue: the single list of things a role can be allowed to do.

Endpoints name an action (`auth=HasAction(Actions.USERS_MANAGE)`), roles hold
actions, users hold roles. Nothing checks `is_staff` any more - a role with the
right actions is the only way in, superusers aside.

Course-scoped authority (who may grade *this* course) stays with course
membership, because an action name cannot express "professor of course 12".
Actions cover the global, catalogue-wide permissions instead.
"""


class Actions:
    USERS_VIEW = "users.view"
    USERS_MANAGE = "users.manage"
    ROLES_VIEW = "roles.view"
    ROLES_MANAGE = "roles.manage"
    COURSES_VIEW = "courses.view"
    COURSES_MANAGE = "courses.manage"
    COURSE_STAFF_MANAGE = "courses.staff.manage"
    STUDENTS_MANAGE = "students.manage"


#: name -> what holding it lets you do, seeded into RoleAction
ACTION_CATALOGUE: dict[str, str] = {
    Actions.USERS_VIEW: "List and read user accounts",
    Actions.USERS_MANAGE: "Create, edit and delete users, and assign their roles",
    Actions.ROLES_VIEW: "List roles and the actions they hold",
    Actions.ROLES_MANAGE: "Create, edit and delete roles and their actions",
    Actions.COURSES_VIEW: "List and read courses",
    Actions.COURSES_MANAGE: "Create, edit and delete courses",
    Actions.COURSE_STAFF_MANAGE: "Assign professors, head TAs and TAs to a course",
    Actions.STUDENTS_MANAGE: "Enrol and remove students on a course",
}

#: role name -> actions it is seeded with
ROLE_ACTIONS: dict[str, list[str]] = {
    "Admin": list(ACTION_CATALOGUE),
    "Professor": [
        Actions.COURSES_VIEW,
        Actions.COURSE_STAFF_MANAGE,
        Actions.STUDENTS_MANAGE,
        Actions.USERS_VIEW,
    ],
    "Head TA": [
        Actions.COURSES_VIEW,
        Actions.STUDENTS_MANAGE,
        Actions.USERS_VIEW,
    ],
    "TA": [Actions.COURSES_VIEW],
}
