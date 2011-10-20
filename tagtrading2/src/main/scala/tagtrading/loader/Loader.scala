package tagtrading.loader

import org.joda.time.DateTime
import com.weiglewilczek.slf4s.{Logging, Logger}
import akka.actor.Actor._
import akka.actor.{Scheduler, Actor}
import java.util.concurrent.TimeUnit

class Loader extends Actor with Logging {
  var latestContentProcessed: Option[DateTime] = None

  def receive = {
    case "poll" =>
  }

}

object Loader {
  val loader = actorOf[Loader].start()

  def start() = {
    Scheduler.schedule(loader, "poll", 1, 1, TimeUnit.MINUTES)
  }

  def shutdown() { Scheduler.shutdown() }

}