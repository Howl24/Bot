from django import forms

class TrackForm(forms.Form):
    sender_id = forms.CharField(max_length=100,
                                widget=forms.HiddenInput())

    track_id = forms.CharField(max_length=100,
                               widget=forms.HiddenInput())
