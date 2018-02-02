# hrv-social
Social "gamification" website for HRV study participants

# Setup
Copy the file "client/src/environments/environment.ts" to "environments/environment.local.ts". Enter the appropriate values for the userPoolId and the userPoolClientId. If you haven't already set up an [~/.aws/credentials](http://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html) file you can also enter the aws access key and secret key, but it's probably more convenient to set up a .aws directory and store that info there.

In the client directory, run npm install.

Follow the instructions in server/setup/README.md to set up all of the server-side resources you will need.

# Running
In the client directory, use ng serve -e local to run the app using your local environment settings.
