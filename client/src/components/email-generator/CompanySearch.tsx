import React, { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, X } from "lucide-react";

interface CompanySearchProps {
  companies: { name: string }[];
  selectedCompany: string;
  onCompanySelect: (companyName: string) => void;
  loading: boolean;
}

export function CompanySearch({
  companies,
  selectedCompany,
  onCompanySelect,
  loading,
}: CompanySearchProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    setShowDropdown(true);

    if (!value) {
      onCompanySelect("");
    }
  };

  const handleCompanyClick = (companyName: string) => {
    setSearchQuery(companyName);
    setShowDropdown(false);
    onCompanySelect(companyName);
  };

  const handleClear = () => {
    setSearchQuery("");
    setShowDropdown(false);
    onCompanySelect("");
    inputRef.current?.focus();
  };

  const filteredCompanies = searchQuery
    ? companies.filter((company) =>
        company.name.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : companies; // Show all companies when no search query

  return (
    <div className="relative">
      <div className="space-y-2">
        <Label htmlFor="company-search">Search Company</Label>
        <div className="relative">
          <Input
            ref={inputRef}
            id="company-search"
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={() => setShowDropdown(true)}
            placeholder="Click to see all companies or type to search..."
            className="w-full pr-20"
          />
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
            {searchQuery && (
              <button
                onClick={handleClear}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="Clear search"
              >
                <X className="h-4 w-4 text-muted-foreground" />
              </button>
            )}
            {loading && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </div>
        </div>
      </div>

      {showDropdown && (
        <div
          ref={dropdownRef}
          className="absolute z-10 w-full mt-1 bg-background border rounded-md shadow-lg"
        >
          <ScrollArea className="h-60">
            {filteredCompanies.length > 0 ? (
              <div className="py-1">
                {filteredCompanies.map((company) => (
                  <button
                    key={company.name}
                    onClick={() => handleCompanyClick(company.name)}
                    className="w-full px-3 py-2 text-left hover:bg-accent hover:text-accent-foreground transition-colors"
                  >
                    {company.name}
                  </button>
                ))}
              </div>
            ) : (
              <div className="px-3 py-4 text-center text-muted-foreground">
                No companies found
              </div>
            )}
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
