from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class UploadPhotoForm(FlaskForm):
    photo_url = StringField("photo_url", validators=[DataRequired()])
    filename = StringField("filename", validators=[DataRequired()])
    license = SelectField(
        choices=[("cc-by-2.0", "CC-BY"), ("cc-by-sa-2.0", "CC-BY-SA")]
    )
    short_caption = StringField("short_caption", validators=[DataRequired()])

    submit = SubmitField("Upload")
