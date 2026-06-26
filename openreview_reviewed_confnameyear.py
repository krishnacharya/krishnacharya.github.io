import getpass
import re

import openreview


username = 'krishna.acharya@gatech.edu'
password = getpass.getpass('OpenReview password: ')


def _content_value(note, key):
    value = note.content.get(key, '')
    if isinstance(value, dict):
        return value.get('value', '')
    return value


def _conference_and_year(submission, official_review, version):
    venue = _content_value(submission, 'venue') or _content_value(submission, 'venueid')
    if venue:
        venue_text = str(venue).strip()
        year_match = re.search(r'(?:19|20)\d{2}', venue_text)
        conference_name = re.sub(r'[\s,]*(?:19|20)\d{2}.*$', '', venue_text).strip()
        if conference_name or year_match:
            return conference_name or venue_text, year_match.group(0) if year_match else ''

    path = official_review.invitation if version == 1 else getattr(official_review, 'domain', '')
    parts = [part for part in str(path).split('/') if part and part != '-']
    year = next((part for part in parts if re.fullmatch(r'(?:19|20)\d{2}', part)), '')
    conference_name = parts[0] if parts else ''
    if conference_name.endswith('.cc'):
        conference_name = conference_name[:-3]
    return conference_name, year


def _get_own_reviews_with_conference(client):
    baseurl_v1, baseurl_v2 = openreview.tools.get_base_urls(client)
    client_v1 = openreview.Client(baseurl=baseurl_v1, token=client.token)
    client_v2 = openreview.api.OpenReviewClient(baseurl=baseurl_v2, token=client.token)

    notes_v1 = client_v1.get_all_notes(tauthor=True)
    submissions_and_official_reviews = []

    for note in notes_v1:
        if 'Official_Review' not in note.invitation:
            continue
        submission_id = note.forum
        submission = client_v1.get_note(submission_id)
        submissions_and_official_reviews.append((submission, note, 1))

    profile_id = 'Guest' if not getattr(client, 'profile') else getattr(getattr(client, 'profile'), 'id')
    notes_v2 = [] if profile_id == 'Guest' else client_v2.get_all_notes(signature=profile_id, transitive_members=True)

    domain_to_reviewer_invitation_suffix = {
        'TMLR': '/-/Review'
    }

    for note in notes_v2:
        if domain_to_reviewer_invitation_suffix.get(note.domain) is None:
            domain = note.domain
            group = client_v2.get_group(domain)
            reviewer_invitation_suffix = getattr(group, 'content', None)
            if group and reviewer_invitation_suffix:
                reviewer_invitation_suffix = group.content.get('review_name', {}).get('value', None)
            if reviewer_invitation_suffix is None:
                continue
            domain_to_reviewer_invitation_suffix[domain] = '/-/' + reviewer_invitation_suffix

        reviewer_invitation_suffix = domain_to_reviewer_invitation_suffix[note.domain]

        official_review = None
        for invitation in note.invitations:
            if reviewer_invitation_suffix in invitation:
                official_review = note
        if official_review is None:
            continue
        submission_id = official_review.forum
        submission = client_v2.get_note(submission_id)
        submissions_and_official_reviews.append((submission, official_review, 2))

    links = []
    for submission, official_review, version in submissions_and_official_reviews:
        submission_link = f'https://openreview.net/forum?id={submission.id}'
        review_link = f'https://openreview.net/forum?id={submission.id}&noteId={official_review.id}'
        if version == 1:
            submission_title = submission.content.get('title', '')
        else:
            submission_title = submission.content.get('title', {}).get('value', '')
        conference_name, conference_year = _conference_and_year(submission, official_review, version)
        links.append({
            'submission_title': submission_title,
            'conference_name': conference_name,
            'conference_year': conference_year,
            'submission_link': submission_link,
            'review_link': review_link,
        })

    return links


client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username=username,
    password=password,
)

result = _get_own_reviews_with_conference(client)
for item in result:
    print(item)