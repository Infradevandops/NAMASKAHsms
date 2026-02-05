/**
 * Module Loader - Handles dynamic module loading with caching
 * Implements hybrid loading strategy: eager load core, lazy load optional
 */

const loadedModules = {}
const loadingPromises = {}

/**
 * Load a module dynamically
 * @param {string} moduleName - Name of the module to load
 * @returns {Promise} - Module promise
 */
export async function loadModule(moduleName) {
  // Return cached module if available
  if (loadedModules[moduleName]) {
    return loadedModules[moduleName]
  }

  // Return existing loading promise if in progress
  if (loadingPromises[moduleName]) {
    return loadingPromises[moduleName]
  }

  // Create new loading promise
  const loadPromise = (async () => {
    try {
      const module = await import(`./modules/${moduleName}.js`)
      loadedModules[moduleName] = module
      delete loadingPromises[moduleName]
      return module
    } catch (error) {
      delete loadingPromises[moduleName]
      console.error(`Failed to load module: ${moduleName}`, error)
      throw error
    }
  })()

  loadingPromises[moduleName] = loadPromise
  return loadPromise
}

/**
 * Preload a module in the background
 * @param {string} moduleName - Name of the module to preload
 */
export function preloadModule(moduleName) {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => loadModule(moduleName))
  } else {
    setTimeout(() => loadModule(moduleName), 2000)
  }
}

/**
 * Get a loaded module synchronously (if available)
 * @param {string} moduleName - Name of the module
 * @returns {Object|null} - Module or null if not loaded
 */
export function getLoadedModule(moduleName) {
  return loadedModules[moduleName] || null
}

/**
 * Clear module cache
 * @param {string} moduleName - Name of the module (optional)
 */
export function clearModuleCache(moduleName) {
  if (moduleName) {
    delete loadedModules[moduleName]
  } else {
    Object.keys(loadedModules).forEach(key => delete loadedModules[key])
  }
}

/**
 * Load multiple modules in parallel
 * @param {string[]} moduleNames - Array of module names
 * @returns {Promise<Object>} - Object with loaded modules
 */
export async function loadModules(moduleNames) {
  const promises = moduleNames.map(name => loadModule(name))
  const modules = await Promise.all(promises)
  
  const result = {}
  moduleNames.forEach((name, index) => {
    result[name] = modules[index]
  })
  
  return result
}

/**
 * Preload multiple modules
 * @param {string[]} moduleNames - Array of module names
 */
export function preloadModules(moduleNames) {
  moduleNames.forEach(name => preloadModule(name))
}
