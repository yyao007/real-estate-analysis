To run the crawler as a deamon, use screen to do that.
```
$ ./start.sh 
```

# BiggerPockets

There are two tables to store the data:

### forumposts:
```
+-------------+--------------+------+-----+---------+-------+
| Field       | Type         | Null | Key | Default | Extra |
+-------------+--------------+------+-----+---------+-------+
| URL         | varchar(500) | NO   | PRI |         |       |
| replyid     | int(11)      | NO   | PRI | NULL    |       |
| pid         | int(11)      | YES  |     | NULL    |       |
| title       | varchar(500) | YES  |     | NULL    |       |
| category    | varchar(500) | YES  |     | NULL    |       |
| categoryURL | varchar(500) | YES  |     | NULL    |       |
| uid         | varchar(50)  | YES  | MUL | NULL    |       |
| replyTo     | int(11)      | YES  |     | NULL    |       |
| postTime    | datetime     | YES  | MUL | NULL    |       |
| body        | text         | YES  |     | NULL    |       |
| likes       | int(11)      | YES  |     | NULL    |       |
| tags        | varchar(500) | YES  |     | NULL    |       |
| city        | varchar(100) | YES  | MUL | NULL    |       |
| state       | varchar(50)  | YES  |     | NULL    |       |
+-------------+--------------+------+-----+---------+-------+
```
### forumusers:
```
+------------+--------------+------+-----+-------------------+----------------+
| Field      | Type         | Null | Key | Default           | Extra          |
+------------+--------------+------+-----+-------------------+----------------+
| uid        | int(11)      | NO   | PRI | NULL              | auto_increment |
| firstName  | varchar(20)  | YES  |     | NULL              |                |
| lastName   | varchar(20)  | YES  |     | NULL              |                |
| source     | varchar(100) | YES  |     | NULL              |                |
| colleagues | int(11)      | YES  |     | NULL              |                |
| followers  | int(11)      | YES  |     | NULL              |                |
| following  | int(11)      | YES  |     | NULL              |                |
| numPosts   | int(11)      | YES  |     | NULL              |                |
| numVotes   | int(11)      | YES  |     | NULL              |                |
| numAwards  | int(11)      | YES  |     | NULL              |                |
| account    | varchar(10)  | YES  |     | NULL              |                |
| city       | varchar(100) | YES  |     | NULL              |                |
| state      | varchar(50)  | YES  |     | NULL              |                |
| dateJoined | datetime     | YES  |     | NULL              |                |
| seeking    | text         | YES  |     | NULL              |                |
| experience | text         | YES  |     | NULL              |                |
| occupation | varchar(767) | YES  |     | NULL              |                |
| goals      | text         | YES  |     | NULL              |                |
| crawl_time | datetime     | YES  |     | CURRENT_TIMESTAMP |                |
+------------+--------------+------+-----+-------------------+----------------+
```
