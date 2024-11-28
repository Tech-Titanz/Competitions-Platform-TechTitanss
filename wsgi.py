import click, pytest, sys, csv,os
from datetime import datetime
from flask import Flask
from flask.cli import with_appcontext, AppGroup
from App.database import db, get_migrate
from App.models import User, Competition, Result, Participant
from App.main import create_app
from App.controllers.commands import DeleteCompetitionCommand,ImportCompetitionsCommand,ImportResultsCommand, UpdateCompetitionCommand,CreateCompetitionsCommand,ViewLeaderboardCommand, ViewProfileCommand
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
            click.echo(f"ID: {competition.id}, Name: {competition.name}, Date: {competition.date}")
    else:
        click.echo("No competitions found.")

@competition_cli.command("import", help="Import competitions from a CSV file")
@click.argument('competition_file')
def import_competitions_cli(competition_file):
    command = ImportCompetitionsCommand(competition_file)
    try:
        command.execute()
        click.echo("Competitions imported successfully.")
    except Exception as e:
        click.echo(f"An error occurred: {e}")

@competition_cli.command("import-results", help="Import results from a CSV file")
@click.argument('results_file')
def import_results_cli(results_file):
    command = ImportResultsCommand(results_file)
    try:
        command.execute()
        click.echo("Results imported successfully.")
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
        
 
@app.cli.command("calculate-aggregate-ranking", help="Calculate Aggregate Profile Ranking")
@click.option("--competition-id", type=int, help="Filter by specific competition ID")
@click.option("--output-file", type=str, help="Path to save the ranking results (optional)")
def calculate_aggregate_ranking_cli(competition_id=None, output_file=None):
    """
    Command to calculate aggregate profile ranking.
    """
    try:
        if competition_id:
            competitions = Competition.query.filter_by(id=competition_id).all()
        else:
            competitions = Competition.query.all()

        if not competitions:
            click.echo("No competitions found matching the criteria.")
            return

     
        rankings = []
        for comp in competitions:
            results = Result.query.filter_by(competition_id=comp.id).all()  # Assuming a `Result` model exists
            for result in results:
                user_id = result.user_id
                score = result.score
                existing = next((r for r in rankings if r['user_id'] == user_id), None)
                if existing:
                    existing['total_score'] += score
                else:
                    rankings.append({"user_id": user_id, "total_score": score})

        rankings.sort(key=lambda x: x["total_score"], reverse=True)

        click.echo("Aggregate Profile Rankings:")
        for rank, entry in enumerate(rankings, start=1):
            user = User.query.get(entry['user_id'])
            click.echo(f"{rank}. {user.username} - {entry['total_score']} points")  # Replace `username` if needed

        if output_file:
            with open(output_file, "w") as f:
                for rank, entry in enumerate(rankings, start=1):
                    user = User.query.get(entry['user_id'])
                    f.write(f"{rank}. {user.username} - {entry['total_score']} points\n")
            click.echo(f"Rankings saved to {output_file}")

    except FileNotFoundError as e:
        click.echo(f"File not found: {e.filename}")
    except Exception as e:
        click.echo(f"An error occurred: {e}")


app.cli.add_command(competition_cli)


# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
def create_user_command(username, password):
    create_user(username, password)
    print(f'{username} created!')

# this command will be : flask user create bob bobpass
@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

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
