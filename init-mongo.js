use("results");
db.createCollection("query1");
db.createCollection("query2.1");
db.createCollection("query2.2");
db.createCollection("query3");
db.createCollection("performance");
db.createUser({
    user: "spark_user",
    pwd: "spark_password",
    roles: [{
        role :"readWrite",
        db: "results"
    }],
});