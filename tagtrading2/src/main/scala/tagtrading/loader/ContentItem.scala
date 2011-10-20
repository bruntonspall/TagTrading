package tagtrading.loader

import com.novus.salat._
import global._
import annotations._
import tagtrading.MongoStorage
import com.novus.salat.dao.SalatDAO

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
dividend: Int,
dividend_history: List[Int]
                )
object Tag extends SalatDAO[Tag,String](collection = MongoStorage.collection("tags"))

case class Offer(
@Key("_id") id:String,
tag: Tag,
price: Int
                  )
object Offer extends SalatDAO[Offer,String](collection = MongoStorage.collection("offers"))