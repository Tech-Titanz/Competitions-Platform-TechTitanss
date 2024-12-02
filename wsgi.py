import click, pytest, sys, csv,os
from datetime import datetime
from flask import Flask
from flask.cli import with_appcontext, AppGroup
from App.database import db, get_migrate
from App.models import User, Competition, Result, Participant
from App.main import create_app
from App.controllers.commands import *
from App.controllers import (
    create_user, 
    get_all_users_json, 
    get_all_users, 
    initialize, 
)

# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database intialized')

'''
User Commands
'''

#Competition Commands Changed to use Command.py classes and methods
competition_cli = AppGroup('competition', help='Competition-related commands')

@competition_cli.command("create", help="Create a new competition")
@click.argument('name')
@click.argument('date')
@click.argument('description', default="")
@click.argument('participants_amount', default=0, type=int)
@click.argument('duration', default=0, type=int)
def create_competition_cli(name, date, description, participants_amount, duration):
    command = CreateCompetitionsCommand(name, description, date, participants_amount, duration)
    error, competition = command.execute()
    if error:
        click.echo(f"Error: {error}")
    else:
        click.echo(f"Competition created: ID={competition.id}, Name={competition.name}")


@competition_cli.command("update", help="Update an existing competition")
@click.argument('competition_id', type=int)
@click.argument('new_name')
@click.argument('new_date')
def update_competition_cli(competition_id, new_name, new_date):
    command = UpdateCompetitionCommand(competition_id, new_name, new_date)
    error, competition = command.execute()
    if error:
        click.echo(f"Error: {error}")
    else:
        click.echo(f"Competition updated: ID={competition.id}, New Name={competition.name}, New Date={competition.date}")


@competition_cli.command("update-participant", help="Update an existing participant")
@click.argument('user_id', type=int)
@click.argument('new_name', type=str, default=None, required=False)  # Optional argument
@click.argument('new_competition_id', type=int, default=None, required=False)  # Optional argument
def update_participant_cli(user_id, new_name, new_competition_id):
    
    command = UpdateParticipantCommand(user_id, new_name, new_competition_id)
    error, user = command.execute()

    if error:
        click.echo(error)
    else:
        click.echo(f"User ID {user_id} has been updated.")
        if new_name:
            click.echo(f"New username: {user.username}")
        if new_competition_id:
            click.echo(f"New competition ID: {new_competition_id}")


@competition_cli.command("delete", help="Delete a competition by ID")
@click.argument('competition_id', type=int)
def delete_competition_cli(competition_id):
    command = DeleteCompetitionCommand(competition_id)
    error, message = command.execute()
    if error:
        click.echo(f"Error: {error}")
    else:
        click.echo(message)

@competition_cli.command("view", help="View all competitions")
def view_competitions_cli():
    competitions = Competition.query.all()
    if competitions:
        for competition in competitions:
            click.echo(f"ID: {competition.id}, Name: {competition.name}, Date: {competition.date}, Duration: {competition.duration}, Description: {competition.description}, Amount: {competition.participants_amount}")
    else:
        click.echo("No competitions found.")
        
        
@competition_cli.command("view-comp-participant", help="View participants for Competitions")
@click.argument("competition_id", type=int)
def view_competition_participant(competition_id):
    command = ViewCompetitionParticipantsCommand(competition_id)
    
    
    error, participants = command.execute()
    
    
    if error:
        click.echo(error)
        return
    
 
    click.echo(f"Participants in Competition {competition_id}:")
    for participant in participants:
        user = User.query.get(participant.user_id)  
        
        if user:
            click.echo(f"Name: {user.username}, ID: {user.id}")
        else:
            click.echo(f"Warning: No user found for participant ID {participant.id} (user_id: {participant.user_id}).")

    
        
@competition_cli.command("view_leaderboard", help="View the leaderboard of all users")
@click.argument('competition_id', default=None, type=int, required=False)
def view_leaderboard_cli(competition_id):
    command = ViewLeaderboardCommand(competition_id=competition_id)  # Pass competition_id to command
    leaderboard_data = command.execute()

    if not leaderboard_data:
        click.echo("No leaderboard data found.")
    else:
        click.echo("Leaderboard:")
        rank = 1
        for participant_name, total_score,comp_participate in leaderboard_data:
            click.echo(f"Rank: {rank}, {participant_name}, Score: {total_score}, {competition_id}, Number of events: {comp_participate}")
            rank += 1
        
@competition_cli.command("add_results", help="Add or update results for a user in a competition")
@click.argument('user_id', type=int)
@click.argument('competition_id', type=int)
@click.argument('new_score', type=int)
def add_results_cli(user_id, competition_id, new_score):
    command = AddCompetitionResultsCommand(user_id, competition_id, new_score)
    command.execute()
    


        


@competition_cli.command("import", help="Import competitions, participants, and results from CSV files")
@click.argument('competition_file')
@click.argument('participant_file')
@click.argument('results_file')
def import_all_cli(competition_file, participant_file, results_file):
    try:
        # Import Competitions
        click.echo("Importing competitions...")
        competition_command = ImportCompetitionsCommand(competition_file)
        competition_command.execute()
        
        # Import Participants
        click.echo("Importing participants...")
        participant_command = ImportParticipantsCommand(participant_file)
        participant_command.execute()
        
        # Import Results
        click.echo("Importing results...")
        results_command = ImportResultsCommand(results_file)
        results_command.execute()
        
        click.echo("All data imported successfully!")
        
    except Exception as e:
        click.echo(f"An error occurred: {e}")

@competition_cli.command("view-results", help="View results from competitions")
@click.argument('results_file')
@click.argument('competitions_file')
def view_results_cli(results_file, competitions_file):
    try:
        competition_mapping = {}
        with open(competitions_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                competition_id = row['id']
                competition_name = row['name']
                competition_mapping[competition_id] = competition_name

        with open(results_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            click.echo("Participant Name, Score, Competition Name")
            click.echo("-" * 40)
            for row in reader:
                participant_name = row['participant_name']
                score = row['score']
                competition_id = row['competition_id']

                competition_name = competition_mapping.get(competition_id, "Unknown Competition")
                click.echo(f'{participant_name}, {score}, {competition_name}')
    except FileNotFoundError as e:
        click.echo(f"File not found: {e.filename}")
    except Exception as e:
        click.echo(f"An error occurred: {e}")
        
 
@competition_cli.command("calculate-aggregate", help="Calculate Aggregate Profile Ranking")
@click.option("--competition-id", type=int, help="Filter by specific competition ID (optional)")
@click.option("--output-file", type=str, help="Path to save the ranking results (optional)")
def calculate_aggregate_ranking_cli(competition_id=None, output_file=None):
    try:
      
        command = AggregateProfileCommand(competition_id=competition_id)

        rankings = command.execute()

        if output_file:
            with open(output_file, "w") as f:
                for rank, (participant_name, total_score, competitions_participated) in enumerate(rankings, start=1):
                    f.write(f"Rank {rank}: {participant_name} - Total Score: {total_score}, Competitions: {competitions_participated}\n")
            click.echo(f"Rankings saved to {output_file}")

        # Display the rankings in the console
        click.echo("Aggregate Profile Rankings:")
        for rank, (participant_name, total_score, competitions_participated) in enumerate(rankings, start=1):
            click.echo(f"Rank {rank}: {participant_name} - Total Score: {total_score}, Competitions: {competitions_participated}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")
        
        




app.cli.add_command(competition_cli)


# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
# @user_cli.command("create", help="Creates a user")
# @click.argument("username", default="rob")
# @click.argument("password", default="robpass")
# def create_user_command(username, password):
#     create_user(username, password)
#     print(f'{username} created!')




# this command will be to create a new admin/moderator user
@user_cli.command("create", help="Create a user")
@click.argument("username",default="rob")
@click.argument("password",default = "robpass")
@click.option('--moderator', is_flag=True, default=False, help="Create as a moderator")
def create_user_command(username, password, moderator):
    # Use the moderator flag to set the user role
    is_moderator = moderator
    command = RegisterUserCommand(username, password, is_moderator=is_moderator)
   
    try:
       new_user = command.execute()
       role = "moderator" if is_moderator else "regular user"
       click.echo(f"User {new_user.username} created as {role}.")
    except Exception as error:
        click.echo(f"Error:{error}")       
  

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())
        
@user_cli.command("view_profile", help="View the profile of a user")
@click.argument('user_id', type=int)
def view_profile_cli(user_id):
    command = ViewProfileCommand(user_id)
    profile_details = command.execute()

    if not profile_details:
        click.echo(f"Error: User with ID {user_id} not found.")
    else:
        click.echo(f"Username: {profile_details['username']}")
        click.echo(f"Rank: {profile_details['rank']}")
        click.echo("Competitions:")
        for competition in profile_details['competitions']:
            click.echo(f"  - {competition['competition_name']}, Score: {competition['score']}, Date: {competition['date']}")

        
@user_cli.command("join", help="Join a competition")
@click.argument("username")
@click.argument("competition_id", type=int)
def join_competition_command(username, competition_id):
  
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f"Error: User '{username}' not found.")
        return

    command = JoinCompetitionCommand(user.id, competition_id)
    error, competition = command.execute()

    if error:
        click.echo(f"Error: {error}")
    else:
        click.echo(f"User {user.username} successfully joined the competition '{competition.name}'!")

app.cli.add_command(user_cli) # add the group to the cli

'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
        
        
@test.command("competition", help="Run Competition tests")
@click.argument("type", default="all")
def competition_tests_command(type):
    if type == "unit":
        # Run only unit tests for competitions
        sys.exit(pytest.main(["App/tests/test_competition.py"]))
    elif type == "int":
        # Run only integration tests for competitions
        sys.exit(pytest.main(["App/tests/test_competition_integration.py"]))
    else:
        # Run all tests related to competition
        sys.exit(pytest.main(["App/tests"]))
