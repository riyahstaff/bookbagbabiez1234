import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

const labelClasses = "text-xs font-medium text-slate-600";
const controlClasses = "rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-900 focus:border-slate-500 focus:outline-none";

function slugId(label: string): string {
  return `field-${label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")}`;
}

export function TextField({
  label,
  id,
  className,
  ...props
}: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  const inputId = id ?? slugId(label);
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className={labelClasses}>
        {label}
      </label>
      <input id={inputId} className={`${controlClasses} ${className ?? ""}`} {...props} />
    </div>
  );
}

export function TextAreaField({
  label,
  id,
  className,
  ...props
}: { label: string } & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const inputId = id ?? slugId(label);
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className={labelClasses}>
        {label}
      </label>
      <textarea id={inputId} className={`${controlClasses} ${className ?? ""}`} {...props} />
    </div>
  );
}

export function SelectField({
  label,
  id,
  className,
  children,
  ...props
}: { label: string; children: ReactNode } & SelectHTMLAttributes<HTMLSelectElement>) {
  const inputId = id ?? slugId(label);
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className={labelClasses}>
        {label}
      </label>
      <select id={inputId} className={`${controlClasses} ${className ?? ""}`} {...props}>
        {children}
      </select>
    </div>
  );
}

export function CheckboxField({
  label,
  className,
  ...props
}: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700">
      <input type="checkbox" className={`h-4 w-4 rounded border-slate-300 ${className ?? ""}`} {...props} />
      {label}
    </label>
  );
}
