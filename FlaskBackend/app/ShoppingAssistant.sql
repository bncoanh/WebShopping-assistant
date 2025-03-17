CREATE TABLE IF NOT EXISTS `Product` (
  `productId` bigint,
  `origin` char(30),
  `imgURL` text,
  `name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `link` text NOT NULL,
  `quantitySold` int NOT NULL,
  `price` decimal(15,2) NOT NULL,
  `reviewCount` int NOT NULL,
  `rating` decimal(2,1) NOT NULL,
  `sellerName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `brandName` char(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `createAt` datetime DEFAULT (now()),
  PRIMARY KEY (`productId`, `origin`)
);

CREATE TABLE IF NOT EXISTS `Category` (
  `categoryId` bigint,
  `origin` char(30),
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `imgURL` text,
  `isLeaf` bool NOT NULL,
  `parentId` bigint,
  `parentOrigin` char(30),
  `createAt` datetime DEFAULT (now()),
  PRIMARY KEY (`categoryId`, `origin`),
  FOREIGN KEY (`parentId`, `parentOrigin`) REFERENCES `Category` (`categoryId`, `origin`)
);

CREATE TABLE IF NOT EXISTS `Product_Category` (
  `productId` bigint,
  `categoryId` bigint,
  `productOrigin` char(30),
  `categoryOrigin` char(30),
  `createAt` datetime DEFAULT (now()),
  PRIMARY KEY (`productId`, `categoryId`, `productOrigin`, `categoryOrigin`),
  FOREIGN KEY (`productId`, `productOrigin`) REFERENCES `Product` (`productId`, `origin`),
  FOREIGN KEY (`categoryId`, `categoryOrigin`) REFERENCES `Category` (`categoryId`, `origin`)
);

-- CREATE TABLE IF NOT EXISTS `Review` (
--   `reviewId` bigint,
--   `origin` char(30),
--   `rating` int NOT NULL,
--   `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
--   `productId` int NOT NULL,
--   `createAt` datetime DEFAULT (now()),
--   PRIMARY KEY (`reviewId`, `origin`),
--   FOREIGN KEY (`productId`, `origin`) REFERENCES `Product` (`productId`, `origin`)
-- );

CREATE TABLE IF NOT EXISTS `Account` (
  `accountId` int PRIMARY KEY AUTO_INCREMENT,
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci UNIQUE NOT NULL,
  `password` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `isAdmin` bool NOT NULL,
  `createAt` datetime DEFAULT (now()),
  `updateAt` datetime DEFAULT (now())
);

CREATE TABLE IF NOT EXISTS `BrowseHistory` (
  `browseId` int PRIMARY KEY AUTO_INCREMENT,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `accountId` int NOT NULL,
  `createAt` datetime DEFAULT (now()),
  FOREIGN KEY (`accountId`) REFERENCES `Account` (`accountId`)
);

CREATE TABLE IF NOT EXISTS `ProductHistory` (
  `accountId` int,
  `productId` bigint,
  `origin` char(30),
  `createAt` datetime DEFAULT (now()),
  PRIMARY KEY (`accountId`, `productId`, `origin`),
  FOREIGN KEY (`accountId`) REFERENCES `Account` (`accountId`),
  FOREIGN KEY (`productId`, `origin`) REFERENCES `Product` (`productId`, `origin`)
);