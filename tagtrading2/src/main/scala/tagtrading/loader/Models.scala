package tagtrading.loader

import com.novus.salat._
import global._
import annotations._
import tagtrading.MongoStorage
import com.novus.salat.dao.SalatDAO
import collection.mutable.HashMap
import org.joda.time.DateTime

case class Dividend(
@Key("_id") id:String,
date: DateTime,
price: Int
                     )
object Dividend extends SalatDAO[Dividend,String](collection = MongoStorage.collection("dividends"))

case class User(
@Key("_id") id: String,
name: String,
grauniads: Int
                 )
object User extends SalatDAO[User,String](collection = MongoStorage.collection("users"))

case class Tag(
@Key("_id") id:String,
name: String,
price: Int,
dividends: List[Dividend]
                )
object Tag extends SalatDAO[Tag,String](collection = MongoStorage.collection("tags"))

case class BuyOffer(
@Key("_id") id:String,
user: User,
tag: Tag,
price: Int
                  )
object BuyOffer extends SalatDAO[BuyOffer,String](collection = MongoStorage.collection("buyoffers"))

case class SellOffer(
@Key("_id") id:String,
user: User,
tag: Tag,
price: Int
                 )
object SellOffer extends SalatDAO[SellOffer,String](collection = MongoStorage.collection("selloffers"))

case class Actions(
@Key("_id") id:String,
user: User,
date: DateTime,
description: String
                 )
object Actions extends SalatDAO[Actions,String](collection = MongoStorage.collection("actions"))