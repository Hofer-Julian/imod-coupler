package _Self

import _Self.buildTypes.*
import _Self.vcsRoots.*
import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.Project

object Project : Project({
    description = "Python scripts coupling components"

    vcsRoot(ImodCouplerImod55)
    vcsRoot(ImodCouplerImod54)
    vcsRoot(MetaSwapLookupTable)
    vcsRoot(ImodCoupler)
    vcsRoot(ImodCouplerImod56)

    buildType(TestbenchCouplerWin64Lumbricus)
    buildType(TestbenchCouplerWin64Release)
    buildType(TestbenchCouplerWin64_2)
    buildType(MakeGitHubRelease)

    template(Linux)
    template(Windows)

    subProject(Primod.Project)
    subProject(IMODCollector.Project)
})
