# AWS EC2 Cloud Pipeline - Operational Guide (AWS Academy)

Because you are using an **AWS Academy Learner Lab**, your session will expire and your credentials will reset every time you start a new lab session. 

When you want to process a new batch of ASL words (e.g., 1,000 words), follow these exact steps from top to bottom.

---

## Step 1: Start the Lab & Get the New Key
1. Go to your AWS Academy Learner Lab console in your browser.
2. Click **Start Lab**. Wait until the dot turns green.
3. Click the **i AWS Details** button at the top.
4. Click **Download PEM** to download your new security key.
5. Move the downloaded `labsuser.pem` file into your `aws/` folder inside the Signify project. *(Overwrite the old one!)*
6. In that same "AWS Details" panel, click **AWS CLI** and copy the temporary credentials block. Paste it into your local terminal so your computer has access to the new lab session.

## Step 2: Wake Up The Server
In your local Windows terminal, run this command to turn on the EC2 instance:
```bash
aws ec2 start-instances --instance-ids i-0c9353df59c14c67d
```

## Step 3: Get Your *New* Public IP Address
Whenever you stop and restart an EC2 server, AWS assigns it a brand new Public IP address! Wait about 30 seconds for the server to fully boot up, then run this:
```bash
aws ec2 describe-instances --instance-ids i-0c9353df59c14c67d --query "Reservations[*].Instances[*].PublicIpAddress" --output text
```
*Copy that IP address, you will need it for the next steps.*

## Step 4: Update Your Script Locally
Open `scripts/cloud_pipeline.py` on your computer.
Find the `WORDS = [...]` list at the top of the file, and paste in your 1,000 new words. Save the file.

## Step 5: Upload the Updated Script to EC2
In your local Windows terminal, use the `scp` command to send your updated script to the server. Notice we are pointing it to `aws/labsuser.pem` now!
```bash
scp -i aws/labsuser.pem scripts/cloud_pipeline.py ec2-user@<YOUR_NEW_IP>:~/
```

## Step 6: Connect to the Server and Run It
Connect to your server using SSH:
```bash
ssh -i aws/labsuser.pem ec2-user@<YOUR_NEW_IP>
```
Once you are logged in, run the pipeline! *(Note: The server's hard drive remembered all your pip installations, so you do NOT need to install anything again!)*
```bash
python3 cloud_pipeline.py
```

## Step 7: Shut Down the Server (CRITICAL)
Once the script says `[SUCCESS] Pipeline completed`, your JSONs are safely stored in your S3 bucket.
Disconnect from the server by typing `exit`, then run this command in your local Windows terminal to pause the server and stop the billing:
```bash
aws ec2 stop-instances --instance-ids i-0c9353df59c14c67d
```
