# Product Requirements Document: Daily Stand Up App

*14 June 2025*

A web-based application
Django Web App to act as a backend application
React to act as the front-end application
PostgreSQL database for data storage and retrieval
Celery to manage reminders scheduling
Slack integration to allow the backend application to send messages to a Slack channel via Slack bot
A daily stand up app that manages daily stand up updates for a team that has adopted scrum framework to manage projects
Sends daily stand up reminders, using a Slack bot, for users to share their daily updates at a particular time
For example, it sends the reminders every day at 9am local time
The reminders should be sent to Slack and users respond via Slack to these reminders to share updates that have the stand up questions
The Slack bot reminders will contain questions that are answered step by step i.e.
The bot sends the first question
The team member answers
A seconds question is return as a response
The user responds to the second question and so forth
When users share updates via Slack, those updates are sent back to the web application and recorded i.e. saved in a database
Reminder can be configured to be sent at particular times
Each reminder will have questions which are custom defined and configured. The can questions can be the following in a reminder:
How are you today?
What did you do yesterday?
What will you do today?
Any blockers?
If a person has not submitted their standup dates before end of day, that person should receive hourly reminders
The reminders can stop at 4pm (or time that has been designated to be the stop/end time)
By the end of day, a summary of all standup submissions are sent. This summary includes:
the percentage of people who have sent updates by end of day
The percentage of people who have not sent updates by end of day
Specific people who have not shared the updates by end of day
The admin of the web app is a scrum master who manages a team of people. The scrum master manages users of group to which the daily standup reminders will be sent to
