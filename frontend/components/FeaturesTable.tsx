import React from 'react';
import { Feature } from '../types';
import { EditIcon } from './icons/EditIcon';
import { TrashIcon } from './icons/TrashIcon';
import { CheckIcon } from './icons/CheckIcon';

interface FeaturesTableProps {
  features: Feature[];
  onEdit: (feature: Feature) => void;
  onDelete: (featureId: string) => void;
  onToggleFixed: (featureId: string) => void;
}

const FeaturesTable: React.FC<FeaturesTableProps> = ({ features, onEdit, onDelete, onToggleFixed }) => {
  return (
    <div className="bg-slate-800/50 shadow-lg rounded-xl overflow-hidden border border-slate-700">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-700">
          <thead className="bg-slate-900/70">
            <tr>
              <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-slate-300 uppercase tracking-wider">Actions</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Feature ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Feature Name</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Category</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Video ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Video URL</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Description</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Detected</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">LLM Explanation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {features.map((feature) => (
              <tr 
                key={feature.id} 
                className={`transition-colors duration-200 odd:bg-slate-800/40 even:bg-slate-800/20 hover:bg-slate-700/50 ${feature.isFixed ? '!bg-green-900/30 hover:!bg-green-800/40' : ''}`}
              >
                <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                  <div className="flex items-center justify-center space-x-2">
                    <button onClick={() => onEdit(feature)} className="text-blue-400 hover:text-blue-300 transition-colors" title="Edit Feature">
                      <EditIcon />
                    </button>
                    <button onClick={() => onToggleFixed(feature.id)} className={`${feature.isFixed ? 'text-green-400 hover:text-green-300' : 'text-slate-500 hover:text-slate-300'} transition-colors`} title={feature.isFixed ? 'Mark as Not Fixed' : 'Mark as Fixed'}>
                      <CheckIcon />
                    </button>
                    <button onClick={() => onDelete(feature.id)} className="text-red-500 hover:text-red-400 transition-colors" title="Delete Feature">
                      <TrashIcon />
                    </button>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-400">{feature.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{feature.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{feature.category}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-400">{feature.videoId}</td>
                <td className="px-6 py-4 text-sm text-blue-400 max-w-xs truncate hover:underline">
                  <a href={feature.videoUrl} target="_blank" rel="noopener noreferrer">{feature.videoUrl}</a>
                </td>
                <td className="px-6 py-4 text-sm text-slate-400 max-w-xs truncate">{feature.description}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">{feature.detected}</td>
                <td className="px-6 py-4 text-sm text-slate-400 max-w-xs truncate">{feature.llmExplanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FeaturesTable;