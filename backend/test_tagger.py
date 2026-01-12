from tagger import auto_tag_article

article = """
If a user forgets their password, they can reset it using the
'Forgot Password' link on the login page. A reset link will be
sent to the registered email address.
"""

result = auto_tag_article(article)
print(result)
