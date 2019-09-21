import threading

class BookingThread (threading.Thread):

   def __init__(self, session, offset, days, destination, checkInYear, checkInMonth, checkInDay, checkOutYear, checkOutMonth, checkOutDay, process_hotels):
      threading.Thread.__init__(self)
      self.session = session
      self.offset  = offset
      self.days  = days
      self.destination = destination
      self.checkInYear = checkInYear
      self.checkInMonth = checkInMonth
      self.checkInDay = checkInDay
      self.checkOutYear = checkOutYear
      self.checkOutMonth = checkOutMonth
      self.checkOutDay = checkOutDay
      self.process_hotels = process_hotels

   def run(self):
      self.process_hotels(self.session, self.offset, self.days, self.destination, \
                           self.checkInYear, self.checkInMonth, self.checkInDay, \
                              self.checkOutYear, self.checkOutMonth, self.checkOutDay)

