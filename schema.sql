-- ============================================================
-- Transport Office Database Schema
-- Database: transport_office
-- MySQL 8.0
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------
-- 1. citizen
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `citizen`;
CREATE TABLE `citizen` (
  `citizen_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `date_of_birth` date NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`citizen_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 2. vehicles
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `vehicles`;
CREATE TABLE `vehicles` (
  `vehicle_id` int NOT NULL,
  `registration_number` varchar(20) DEFAULT NULL,
  `manufacture_year` int DEFAULT NULL,
  `citizen_id` int NOT NULL,
  PRIMARY KEY (`vehicle_id`),
  UNIQUE KEY `registration_number` (`registration_number`),
  KEY `citizen_id` (`citizen_id`),
  CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`citizen_id`) REFERENCES `citizen` (`citizen_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 3. driving_license
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `driving_license`;
CREATE TABLE `driving_license` (
  `dl_number` varchar(20) NOT NULL,
  `issue_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `citizen_id` int NOT NULL,
  PRIMARY KEY (`dl_number`),
  KEY `citizen_id` (`citizen_id`),
  CONSTRAINT `driving_license_ibfk_1` FOREIGN KEY (`citizen_id`) REFERENCES `citizen` (`citizen_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 4. vehicle_registrations
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `vehicle_registrations`;
CREATE TABLE `vehicle_registrations` (
  `registration_id` int NOT NULL,
  `registration_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `citizen_id` int NOT NULL,
  PRIMARY KEY (`registration_id`),
  KEY `citizen_id` (`citizen_id`),
  CONSTRAINT `vehicle_registrations_ibfk_1` FOREIGN KEY (`citizen_id`) REFERENCES `citizen` (`citizen_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 5. violations
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `violations`;
CREATE TABLE `violations` (
  `violation_id` int NOT NULL,
  `violation_type` varchar(100) DEFAULT NULL,
  `violation_date` date DEFAULT NULL,
  `fine_amount` decimal(10,2) DEFAULT NULL,
  `vehicle_id` int NOT NULL,
  PRIMARY KEY (`violation_id`),
  KEY `vehicle_id` (`vehicle_id`),
  CONSTRAINT `violations_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 6. tax
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `tax`;
CREATE TABLE `tax` (
  `tax_id` int NOT NULL,
  `tax_type` varchar(50) DEFAULT NULL,
  `tax_amount` decimal(10,2) DEFAULT NULL,
  `due_date` date DEFAULT NULL,
  `vehicle_id` int NOT NULL,
  PRIMARY KEY (`tax_id`),
  KEY `vehicle_id` (`vehicle_id`),
  CONSTRAINT `tax_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 7. payment_info
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `payment_info`;
CREATE TABLE `payment_info` (
  `payment_id` int NOT NULL,
  `payment_date` date DEFAULT NULL,
  `amount_paid` decimal(10,2) DEFAULT NULL,
  `payment_mode` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`payment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 8. liability
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `liability`;
CREATE TABLE `liability` (
  `liability_id` int NOT NULL,
  `liability_type` varchar(20) DEFAULT NULL,
  `reference_id` int NOT NULL,
  `vehicle_id` int NOT NULL,
  PRIMARY KEY (`liability_id`),
  KEY `vehicle_id` (`vehicle_id`),
  CONSTRAINT `liability_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`),
  CONSTRAINT `liability_chk_1` CHECK ((`liability_type` IN ('VIOLATION','TAX')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------
-- 9. paid_using
-- -----------------------------------------------------------
DROP TABLE IF EXISTS `paid_using`;
CREATE TABLE `paid_using` (
  `liability_id` int NOT NULL,
  `payment_id` int NOT NULL,
  PRIMARY KEY (`liability_id`,`payment_id`),
  KEY `payment_id` (`payment_id`),
  CONSTRAINT `paid_using_ibfk_1` FOREIGN KEY (`liability_id`) REFERENCES `liability` (`liability_id`),
  CONSTRAINT `paid_using_ibfk_2` FOREIGN KEY (`payment_id`) REFERENCES `payment_info` (`payment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
