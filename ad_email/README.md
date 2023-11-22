# Email sending module

This module is used to send emails. Requires a logger object as input to the AdEmail class, and the send_email() method can be called to send the email, with recipients (str or list), email_subject, email_message and email_priority arguments supplied.

## Protocol

The send_email() function is called with recipients, email subject, email message and email priority as inputs, and will send an email using those settings.

## Configuration

Settings are imported from [ad_config.py](../config/ad_config.py).

## Usage

This script is configured to be used as a module import as per the following example:

```python
# Create AdEmail object
self.email = AdEmail(self.rf_obj.rf_loggers.sw)

# Render email html message
email_html = self.email.generate_email_html(
    self.rf_obj.runfolder_name, ",".join(set(self.workflows)),
    self.queries, self.sample_count
)
# Send email
self.email.send_email(
    recipients=[ad_config.MAIL_SETTINGS["binfx_recipient"]],
    email_subject=self.pipeline_started_subj,
    email_message=email_html,
    email_priority=1,
)
```

## Logging

The AdEmail class takes a logger as input.

## Testing

**N.B. Tests and test cases/files MUST be maintained and updated accordingly in conjunction with script development**

This script has a full test suite:
* [test_ad_email.py](../test/test_ad_email.py)
  
These tests should be run before pushing any code to ensure all tests in the GitHub Actions workflow pass.