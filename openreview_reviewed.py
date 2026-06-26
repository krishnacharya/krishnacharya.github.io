import getpass

import openreview


username = 'krishna.acharya@gatech.edu'
password = getpass.getpass('OpenReview password: ')

client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=username,
    password=password,
)

result = openreview.tools.get_own_reviews(client)
print(result)