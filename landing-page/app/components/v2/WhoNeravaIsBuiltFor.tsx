import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function WhoNeravaIsBuiltFor() {
  const segments = [
    {
      title: 'EV Drivers',
      items: [
        'Daily commuters who charge regularly and value routine rewards',
        'Tesla owners and drivers of all EV brands',
        'Apartment dwellers with shared charging infrastructure',
        'Suburban families managing multiple vehicles and charging schedules',
        'Urban professionals who charge near work and home',
      ],
    },
    {
      title: 'Merchants',
      items: [
        'Coffee shops perfect for charging wait times',
        'Juice bars and healthy fast-casual restaurants',
        'Gyms and fitness studios near charging hubs',
        'Retail boutiques in high-traffic EV areas',
        'Quick-service restaurants seeking new customer channels',
      ],
    },
    {
      title: 'Charger Hosts',
      items: [
        'Apartment communities with resident charging',
        'Hotels and hospitality offering guest charging',
        'Corporate campuses with employee charging programs',
        'Shopping centers with public charging stations',
      ],
    },
  ]

  return (
    <SectionWrapper className="bg-gray-50">
      <SectionHeader
        title="Who Nerava Is Built For"
        subtitle="We're starting with high-density EV hubs and forward-thinking businesses. Our initial focus is on areas with strong EV adoption, abundant charging infrastructure, and diverse merchant ecosystems. These communities become the foundation for network effects that benefit everyone."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {segments.map((segment, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              {segment.title}
            </h3>
            <ul className="space-y-3">
              {segment.items.map((item, itemIndex) => (
                <li key={itemIndex} className="flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span className="text-gray-600">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}

