from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, DateTimeField, StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class UploadPhotoForm(FlaskForm):
    photo_url = StringField("photo_url", validators=[Data])
    photo_id = StringField("photo_id", validators=[DataRequired()])
    user_id = StringField("user_id", validators=[DataRequired()])
    username = StringField("username", validators=[DataRequired()])
    realname = StringField("realname", validators=[DataRequired()])

    jpeg_url = StringField("jpeg_url", validators=[DataRequired()])
    license_id = SelectField(
        choices=[("cc-by-2.0", "CC-BY"), ("cc-by-sa-2.0", "CC-BY-SA")]
    )

    filename = StringField("filename", validators=[DataRequired()])
    short_caption = StringField("short_caption", validators=[DataRequired()])

    posted_date = DateTimeField("posted_date", validators=[DataRequired()])
    date_taken = DateTimeField("date_taken", validators=[DataRequired()])
    taken_unknown = BooleanField("taken_unknown", validators=[DataRequired()])
    taken_granularity = IntegerField("taken_granularity", validators=[DataRequired()])

    submit = SubmitField("Upload")
