from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from time import time
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, DateType
from datetime import datetime

spark = SparkSession.builder \
  .appName("Query2") \
  .config("spark.mongodb.input.uri", "mongodb://spark_user:spark_password@mongo:27017/results") \
  .config("spark.mongodb.output.uri", "mongodb://spark_user:spark_password@mongo:27017/results") \
  .getOrCreate()

#PARQUET
start = time()

df = spark.read.parquet("hdfs://namenode:8020/disk_data_filtered.parquet") \
  .drop("serial_number", "s9_power_on_hours", "date")
df.cache()

#prima parte
df1 = df.groupBy("model").agg(sum("failure").alias("failures"))\
  .orderBy("failures", ascending=False).limit(10)

#seconda parte
df2 = df.groupBy("vault_id").agg(sum("failure").alias("failures"))
df3 = df.filter(df["failure"] == 1).groupBy("vault_id").agg(collect_set("model").alias("list_of_models"))
df4 = df3.join(df2, "vault_id").orderBy("failures", ascending=False).limit(10)

df1.show()
df4.show()
end = time()

# Save the results of the query
df1.write.format("com.mongodb.spark.sql.DefaultSource") \
  .mode("overwrite") \
  .option("collection", "query2.1") \
  .save()

df4.write.format("com.mongodb.spark.sql.DefaultSource") \
    .mode("overwrite") \
    .option("collection", "query2.2") \
    .save()
  
df.unpersist()

elapsed = end - start

print("Execution time Parquet: ", elapsed)

# Save the performance of the query
perf = spark.createDataFrame([(datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), "Query2", "Parquet", elapsed)], ["Timestamp", "Query", "File format", "Execution time (s)"])

perf.write.format("com.mongodb.spark.sql.DefaultSource") \
  .mode("append") \
  .option("collection", "performance") \
  .save()
  

#CSV
schema = StructType([
    StructField("date", DateType(), True),
    StructField("serial_number", StringType(), True),
    StructField("model", StringType(), True),
    StructField("failure", IntegerType(), True),
    StructField("vault_id", IntegerType(), True),
    StructField("s9_power_on_hours", FloatType(), True),
    ])

start = time()

df = spark.read.csv("hdfs://namenode:8020/disk_data_filtered.csv", header=True, schema=schema) \
  .drop("serial_number", "s9_power_on_hours", "date")
df.cache()

#prima parte
df1 = df.groupBy("model").agg(sum("failure").alias("failures")) \
  .orderBy("failures", ascending=False).limit(10)

#seconda parte
df2 = df.groupBy("vault_id").agg(sum("failure").alias("failures"))
df3 = df.filter(df["failure"] == 1).groupBy("vault_id").agg(collect_set("model").alias("list_of_models"))
df4 = df3.join(df2, "vault_id").orderBy("failures", ascending=False).limit(10)

df1.show()
df4.show()
end = time()

elapsed = end - start
print("Execution time CSV: ", elapsed)

# Save the performance of the query
perf = spark.createDataFrame([(datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), "Query2", "CSV", elapsed)], ["Timestamp", "Query", "File format", "Execution time (s)"])

perf.write.format("com.mongodb.spark.sql.DefaultSource") \
  .mode("append") \
  .option("collection", "performance") \
  .save()

spark.stop()