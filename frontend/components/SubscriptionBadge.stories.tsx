import React from 'react'
import SubscriptionBadge from './SubscriptionBadge'

export default { title: 'Components/SubscriptionBadge' }

export const Free = () => <div className="tier-free"><SubscriptionBadge /></div>
export const Creator = () => <div className="tier-creator"><div className="badge-inner px-3 py-1 rounded-full text-sm font-semibold">CREATOR</div></div>
export const Pro = () => <div className="tier-pro"><div className="badge-inner px-3 py-1 rounded-full text-sm font-semibold">PRO</div></div>
