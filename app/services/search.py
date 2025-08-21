def search_courses(courses, q: str | None):
    if not q:
        return courses
    ql = q.lower()

    def matches(c):
        return (
            ql in (c.title or "").lower()
            or ql in (c.course_code or "").lower()
            or ql in (c.description or "").lower()
            or ql in (c.tags or "").lower()
        )

    return [c for c in courses if matches(c)]