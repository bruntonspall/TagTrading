package bootstrap.liftweb

import net.liftweb.common.Full
import net.liftweb.http._
import tagtrading.loader.Loader
import net.liftweb.util.Props

class Boot {
  def boot() {
    // use html5 not xhtml (lift's default) for both templates and output
    // see http://www.assembla.com/spaces/liftweb/wiki/HtmlProperties_XHTML_and_HTML5
    LiftRules.htmlProperties.default.set((r: Req) => new Html5Properties(r.userAgent))
    LiftRules.addToPackages("tagtrading")
    Loader.start()
    LiftRules.unloadHooks.append { Loader.shutdown _ }
  }
}