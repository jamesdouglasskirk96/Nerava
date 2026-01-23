import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function BuiltToScaleSection() {
  return (
    <SectionWrapper id="built-to-scale" className="bg-gray-50">
      <SectionHeader
        title="Built to scale everywhere people charge"
        subtitle="Today we're solving discovery. Tomorrow we'll connect utilities, incentives, and the entire charging ecosystem."
      />
      
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg p-8 shadow-sm">
          <p className="text-lg text-gray-700 mb-6">
            Nerava starts with the charging moment—helping drivers discover nearby businesses while they wait. But the network we're building opens up much more.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="text-2xl text-primary">•</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  Today: Discovery
                </h3>
                <p className="text-gray-600">
                  Connect drivers with walkable businesses during charging sessions.
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-4">
              <div className="text-2xl text-primary">•</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  Tomorrow: Incentives & Utilities
                </h3>
                <p className="text-gray-600">
                  Grid-friendly charging rewards, utility partnerships, and ecosystem-wide value creation.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionWrapper>
  )
}



