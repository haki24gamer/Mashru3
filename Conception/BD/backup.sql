-- MySQL dump 10.13  Distrib 8.0.41, for Linux (x86_64)
--
-- Host: localhost    Database: Mashru3
-- ------------------------------------------------------
-- Server version	8.0.41-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `assigned`
--

DROP TABLE IF EXISTS `assigned`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assigned` (
  `user_id` int NOT NULL,
  `task_id` int NOT NULL,
  `note` text,
  `created_at` date DEFAULT (curdate()),
  PRIMARY KEY (`user_id`,`task_id`),
  KEY `task_id` (`task_id`),
  CONSTRAINT `assigned_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`),
  CONSTRAINT `assigned_ibfk_2` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assigned`
--

LOCK TABLES `assigned` WRITE;
/*!40000 ALTER TABLE `assigned` DISABLE KEYS */;
INSERT INTO `assigned` VALUES (1,2,NULL,'2025-02-17'),(1,4,NULL,'2025-02-17'),(1,5,NULL,'2025-02-17'),(1,7,'travail','2025-02-18'),(1,8,'travail','2025-02-18'),(2,1,NULL,'2025-02-17'),(2,3,NULL,'2025-02-17'),(2,6,NULL,'2025-02-18'),(2,7,'travail','2025-02-18'),(2,8,'travail','2025-02-18'),(3,6,'do it','2025-02-18');
/*!40000 ALTER TABLE `assigned` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `participate`
--

DROP TABLE IF EXISTS `participate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `participate` (
  `user_id` int NOT NULL,
  `project_id` int NOT NULL,
  `role` varchar(50) NOT NULL,
  `created_at` date DEFAULT (curdate()),
  PRIMARY KEY (`user_id`,`project_id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `participate_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`),
  CONSTRAINT `participate_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `participate`
--

LOCK TABLES `participate` WRITE;
/*!40000 ALTER TABLE `participate` DISABLE KEYS */;
INSERT INTO `participate` VALUES (1,1,'Owner','2025-02-17'),(1,2,'membre','2025-02-18'),(2,1,'membre','2025-02-17'),(2,2,'Owner','2025-02-18'),(2,3,'Membre','2025-02-18'),(3,2,'membre','2025-02-18'),(3,3,'Owner','2025-02-18');
/*!40000 ALTER TABLE `participate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `predecessor`
--

DROP TABLE IF EXISTS `predecessor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `predecessor` (
  `task_id` int NOT NULL,
  `predecessor_id` int NOT NULL,
  `created_at` date DEFAULT (curdate()),
  PRIMARY KEY (`task_id`,`predecessor_id`),
  KEY `predecessor_id` (`predecessor_id`),
  CONSTRAINT `predecessor_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`),
  CONSTRAINT `predecessor_ibfk_2` FOREIGN KEY (`predecessor_id`) REFERENCES `task` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `predecessor`
--

LOCK TABLES `predecessor` WRITE;
/*!40000 ALTER TABLE `predecessor` DISABLE KEYS */;
/*!40000 ALTER TABLE `predecessor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project` (
  `project_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `image` varchar(255) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `finished_date` date DEFAULT NULL,
  `created_at` date DEFAULT (curdate()),
  PRIMARY KEY (`project_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project`
--

LOCK TABLES `project` WRITE;
/*!40000 ALTER TABLE `project` DISABLE KEYS */;
INSERT INTO `project` VALUES (1,'Projet 1','Travaillez bien','img','2025-05-25','2025-05-29',NULL,'2025-02-17'),(2,'Projet 2','travaillez extra bien','img 3','2025-09-05','2025-12-06',NULL,'2025-02-18'),(3,'Projet 3','Tres bon projet','img 4','2025-02-05','2025-06-05',NULL,'2025-02-18');
/*!40000 ALTER TABLE `project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `task`
--

DROP TABLE IF EXISTS `task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task` (
  `task_id` int NOT NULL AUTO_INCREMENT,
  `project_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `priority` enum('low','medium','high') NOT NULL,
  `status` enum('TODO','IN_PROGRESS','REVIEW','DONE') DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `finished_date` date DEFAULT NULL,
  `created_at` date DEFAULT (curdate()),
  PRIMARY KEY (`task_id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `task_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`project_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `task`
--

LOCK TABLES `task` WRITE;
/*!40000 ALTER TABLE `task` DISABLE KEYS */;
INSERT INTO `task` VALUES (1,1,'tache 1','Fait le ','medium','IN_PROGRESS','2025-05-26','2025-05-28',NULL,'2025-02-17'),(2,1,'Tache 2','fait le aussi','high','IN_PROGRESS','2025-05-26','2025-05-28',NULL,'2025-02-17'),(3,1,'tache 3','fait vite','medium','TODO','2025-05-26','2025-05-29',NULL,'2025-02-17'),(4,1,'tache 4','fait vite 4','low','IN_PROGRESS','2025-05-26','2025-05-29',NULL,'2025-02-17'),(5,1,'tache 5','fait vite 6','medium','DONE','2025-05-26','2025-05-29',NULL,'2025-02-17'),(6,2,'tache 1','fait le 1','low','TODO','2025-02-20','2025-06-20',NULL,'2025-02-18'),(7,1,'task','jjjj','low','TODO','2025-05-04','2025-05-09',NULL,'2025-02-18'),(8,1,'task','jjjj','low','TODO','2025-05-04','2025-05-09',NULL,'2025-02-18'),(9,3,'Tache p31','fait le vite','medium','TODO','2025-02-05','2025-06-05',NULL,'2025-02-18'),(10,3,'Tache p31','fait le vite','medium','TODO','2025-02-05','2025-06-05',NULL,'2025-02-18'),(11,3,'Tache p33','fait le vite','medium','IN_PROGRESS','2025-02-05','2025-06-05',NULL,'2025-02-18'),(12,3,'Tache p35','fait le vite','medium','DONE','2025-02-05','2025-06-05',NULL,'2025-02-18'),(13,3,'Tache p36','fait le vite','medium','DONE','2025-02-05','2025-06-05',NULL,'2025-02-18');
/*!40000 ALTER TABLE `task` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `image` varchar(255) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'hagui',NULL,'scrypt:32768:8:1$kvKzHNpky8Qje6wH$e05a0d8c5206cf043def93691d6e81a3f2fe0bdb0526a86dc037deef04cf6059666c2d9ff7df4d0614ca4e647635b3fbeb7ba62f2b59802f76833bf5df35e4f5','hagui@gmail.com'),(2,'haki',NULL,'scrypt:32768:8:1$PMrVyDCpzFSSEMhl$c5a94e68e2035a450cc8af6e7bd042688d4d5b42c6d5854e3a416371c2303050a6b08e8f13e64a0856eeaf93c5f96f829a3dff3ab0b54b7acd69ce68ec228958','haki@gmail.com'),(3,'Ali',NULL,'scrypt:32768:8:1$EuJLGrMJjb4Txhpq$9a110f31cb35e392b14bc8a7cb35580d0a9ec5de2f34a782e00e7297c8ff5b9e5431fd7c50b954cb48a894dbf1c55b65938e5a743c482d7ff4372555668d4231','Ali123@gmail.com'),(4,'abdi',NULL,'scrypt:32768:8:1$s3rzmTgTnrBbrzrQ$6187b866558c5bfa31a2edf468024fa168e0c7d79982859f0d9b8ef82115d8e92fda68241e410294618f0c6c964479c3736899ca4a3edd1a14a34f5a2e11dfb1','Abdi@gmail.com'),(5,'hassan',NULL,'scrypt:32768:8:1$cv29PhmYJuqSAohF$80e267e9274a4649dd49c17e588a57d2bb536a184dbf7ad7415f7a8abdf0b993a2bda539b54a1d107b7f3948478bb225eee488e0048424b29b33eafda4a2aea5','hassan@gmail.com'),(6,'hagui',NULL,'scrypt:32768:8:1$m217S5jqVK4g3few$81bf1e4b21c92e51ded1f71a5420e237eb84b73efdce3d914f35b8401293a1470130613d7f61412899d3a97092d541786c5a5588b59dbc22ffe12b98b14cc8ff','haguimohamed456@gmail.com'),(7,'hagui',NULL,'scrypt:32768:8:1$memF77UYdW5j7U0N$b010b237945a5d6e1cda43c71b4c3f4d2dfb7fcf8f115e2adc144a831c9c71e4d5c367102a7b0e1e5428ed9c7a69585f77492f9c2b57bc15368e1576dc02a0f7','haguimohamed123@gmail.com');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-19 18:09:37
