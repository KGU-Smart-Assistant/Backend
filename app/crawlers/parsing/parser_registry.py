REGISTRY = [
    {
        "name": "kyonggi_notice_detail",
        "url_patterns": ("selectbbsnttview.do",),
        "categories": ("notice", "materials"),
        "parser": "notice_detail",
    },
    {
        "name": "kyonggi_faq_list",
        "url_patterns": ("selectbbsnttlist.do", "faq"),
        "categories": ("faq",),
        "parser": "notice_detail",
    },
    {
        "name": "kyonggi_schedule",
        "url_patterns": ("selecttnschafsschdullistus.do",),
        "categories": ("academic_schedule",),
        "parser": "generic_markdown",
    },
    {
        "name": "generic_markdown",
        "url_patterns": (),
        "categories": (),
        "parser": "generic_markdown",
    },
]
