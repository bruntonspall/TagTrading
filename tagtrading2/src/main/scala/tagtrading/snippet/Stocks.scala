package tagtrading.snippet

import tagtrading.MongoStorage
import tagtrading.loader.Tag
import net.liftweb.util._
import Helpers._
import xml.NodeSeq
import com.mongodb.casbah.commons.MongoDBObject


class Stocks {
  def all = {
    "tr *" #> Tag.find(MongoDBObject()).map { tag =>
        "#stockname" #> tag.name &
        "#stockprice" #> tag.price
      }
  }


}